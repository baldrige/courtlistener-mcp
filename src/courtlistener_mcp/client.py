"""
CourtListener API client for MCP server.
"""

import os
import re
from html import unescape
from functools import lru_cache

import httpx

BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
SEARCH_URL = "https://www.courtlistener.com/api/rest/v3/search/"


def get_api_token() -> str:
    """Get the API token from environment variable."""
    token = os.environ.get("COURTLISTENER_API_TOKEN")
    if not token:
        raise ValueError(
            "COURTLISTENER_API_TOKEN environment variable not set. "
            "Get your token at https://www.courtlistener.com/profile/api/"
        )
    return token


def get_headers() -> dict[str, str]:
    """Get headers for authenticated API requests."""
    return {
        "Authorization": f"Token {get_api_token()}",
        "Content-Type": "application/json",
    }


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Court shortcuts for common queries
COURT_SHORTCUTS = {
    "scotus": "scotus",
    "supreme": "scotus",
    "1st": "ca1",
    "2nd": "ca2",
    "3rd": "ca3",
    "4th": "ca4",
    "5th": "ca5",
    "6th": "ca6",
    "7th": "ca7",
    "8th": "ca8",
    "9th": "ca9",
    "10th": "ca10",
    "11th": "ca11",
    "dc": "cadc",
    "federal": "cafc",
}


def resolve_court(court: str) -> str:
    """Resolve court shortcut to CourtListener court ID."""
    return COURT_SHORTCUTS.get(court.lower(), court.lower())


class CourtListenerClient:
    """Async client for CourtListener API."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=get_headers(),
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        endpoint: str,
        params: dict | None = None,
        base_url: str = BASE_URL,
    ) -> dict:
        """Make an authenticated GET request."""
        client = await self._get_client()
        url = f"{base_url}{endpoint}"
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def search_opinions(
        self,
        query: str,
        court: str | None = None,
        date_after: str | None = None,
        date_before: str | None = None,
        limit: int = 20,
        semantic: bool = False,
    ) -> dict:
        """
        Search for court opinions.

        Args:
            query: Search terms (or plain language for semantic search)
            court: Court ID or shortcut
            date_after: Filter by date (YYYY-MM-DD)
            date_before: Filter by date (YYYY-MM-DD)
            limit: Maximum results
            semantic: Use semantic search instead of keyword search

        Returns:
            Search results with case metadata
        """
        params = {
            "q": query,
            "type": "o",
            "order_by": "score desc",
        }

        if semantic:
            params["semantic"] = "true"
        if court:
            params["court"] = resolve_court(court)
        if date_after:
            params["filed_after"] = date_after
        if date_before:
            params["filed_before"] = date_before

        client = await self._get_client()
        response = await client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "case_name": item.get("caseName"),
                "citation": item.get("citation", [None])[0] if item.get("citation") else None,
                "date_filed": item.get("dateFiled"),
                "court": item.get("court"),
                "cluster_id": item.get("cluster_id"),
                "opinion_id": item.get("id"),
                "snippet": strip_html(item.get("snippet", "")),
                "url": f"https://www.courtlistener.com/opinion/{item.get('cluster_id')}/",
            })

        return {
            "count": data.get("count", 0),
            "showing": len(results),
            "results": results,
            "search_type": "semantic" if semantic else "keyword",
        }

    async def get_opinion(self, opinion_id: int) -> dict:
        """
        Fetch an opinion by ID.

        Args:
            opinion_id: The opinion ID

        Returns:
            Opinion data including full text
        """
        data = await self._request(f"opinions/{opinion_id}/")

        # Get cluster for metadata
        cluster_data = {}
        if data.get("cluster"):
            cluster_id = data["cluster"].rstrip("/").split("/")[-1]
            cluster_data = await self._request(f"clusters/{cluster_id}/")

        # Extract text
        text = ""
        for field in ["plain_text", "html_with_citations", "html", "html_lawbox"]:
            if data.get(field):
                text = data[field]
                if field.startswith("html"):
                    text = strip_html(text)
                break

        return {
            "case_name": cluster_data.get("case_name") or data.get("case_name", "Unknown"),
            "citation": cluster_data.get("citation_string"),
            "court": cluster_data.get("court"),
            "date_filed": cluster_data.get("date_filed"),
            "judges": cluster_data.get("judges"),
            "author": data.get("author_str"),
            "opinion_id": data.get("id"),
            "cluster_id": cluster_data.get("id"),
            "syllabus": strip_html(cluster_data.get("syllabus", "")),
            "text": text,
            "word_count": len(text.split()) if text else 0,
            "url": f"https://www.courtlistener.com/opinion/{cluster_data.get('id')}/",
        }

    async def lookup_citation(self, citation: str) -> dict:
        """
        Look up a legal citation.

        Args:
            citation: Legal citation (e.g., "410 U.S. 113")

        Returns:
            Matching case details
        """
        # Parse citation pattern
        pattern = r"(\d+)\s+([A-Za-z\.\s]+?)\s+(\d+)"
        match = re.search(pattern, citation)

        if match:
            query = f'citation:"{match.group(1)} {match.group(2).strip()} {match.group(3)}"'
        else:
            query = f'"{citation}"'

        params = {
            "q": query,
            "type": "o",
            "order_by": "score desc",
        }

        client = await self._get_client()
        response = await client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return {
                "found": False,
                "query": citation,
                "message": "No matching cases found",
            }

        matches = []
        for item in results[:5]:
            matches.append({
                "case_name": item.get("caseName"),
                "citation": item.get("citation", []),
                "date_filed": item.get("dateFiled"),
                "court": item.get("court"),
                "cluster_id": item.get("cluster_id"),
                "opinion_id": item.get("id"),
                "url": f"https://www.courtlistener.com/opinion/{item.get('cluster_id')}/",
            })

        return {
            "found": True,
            "query": citation,
            "count": len(matches),
            "matches": matches,
        }

    async def get_opinion_pdf(self, opinion_id: int, save_path: str | None = None) -> dict:
        """
        Get the PDF URL for an opinion and optionally download it.

        Args:
            opinion_id: The opinion ID
            save_path: Optional path to save the PDF file

        Returns:
            Dict with PDF URL and download status
        """
        data = await self._request(f"opinions/{opinion_id}/")

        pdf_url = data.get("download_url")
        if not pdf_url:
            return {
                "opinion_id": opinion_id,
                "has_pdf": False,
                "message": "No PDF available for this opinion",
            }

        result = {
            "opinion_id": opinion_id,
            "has_pdf": True,
            "pdf_url": pdf_url,
            "page_count": data.get("page_count"),
        }

        # Download if path provided
        if save_path:
            client = await self._get_client()
            response = await client.get(pdf_url)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)

            result["saved_to"] = save_path
            result["file_size_bytes"] = len(response.content)

        return result

    async def list_courts(self) -> dict:
        """
        List available courts.

        Returns:
            Dictionary of court IDs and names
        """
        courts = []
        url = f"{BASE_URL}courts/"

        client = await self._get_client()
        while url:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            for court in data.get("results", []):
                courts.append({
                    "id": court["id"],
                    "name": court["full_name"],
                    "short_name": court.get("short_name"),
                    "jurisdiction": court.get("jurisdiction"),
                })

            url = data.get("next")

        return {
            "count": len(courts),
            "courts": courts,
            "shortcuts": COURT_SHORTCUTS,
        }
