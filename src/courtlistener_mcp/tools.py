"""
MCP tool definitions for CourtListener.
"""

from mcp.types import Tool

TOOLS = [
    Tool(
        name="search_opinions",
        description=(
            "Search CourtListener for court opinions. Use this to find cases by keyword, "
            "topic, legal doctrine, or party names. Supports filtering by court and date range."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms (e.g., 'qualified immunity', 'first amendment social media')",
                },
                "court": {
                    "type": "string",
                    "description": (
                        "Court ID or shortcut. Examples: 'scotus' (Supreme Court), "
                        "'ca9' (9th Circuit), 'ca5' (5th Circuit), 'cadc' (DC Circuit)"
                    ),
                },
                "date_after": {
                    "type": "string",
                    "description": "Only cases filed after this date (YYYY-MM-DD format)",
                },
                "date_before": {
                    "type": "string",
                    "description": "Only cases filed before this date (YYYY-MM-DD format)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20, max: 50)",
                    "default": 20,
                },
                "semantic": {
                    "type": "boolean",
                    "description": (
                        "Use semantic search instead of keyword search. "
                        "Semantic search accepts plain language queries like "
                        "'cases about whether police can search phones without a warrant'. "
                        "Default is false (keyword search with boolean operators)."
                    ),
                    "default": False,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_opinion",
        description=(
            "Fetch the full text of a court opinion by its ID. Use this after searching "
            "to retrieve the complete opinion text, syllabus, and metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "opinion_id": {
                    "type": "integer",
                    "description": "The opinion ID from a search result",
                },
            },
            "required": ["opinion_id"],
        },
    ),
    Tool(
        name="lookup_citation",
        description=(
            "Resolve a legal citation to find the corresponding case. Use standard legal "
            "citation formats like '410 U.S. 113' or '347 U.S. 483'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "citation": {
                    "type": "string",
                    "description": "Legal citation (e.g., '410 U.S. 113', '123 F.3d 456')",
                },
            },
            "required": ["citation"],
        },
    ),
    Tool(
        name="list_courts",
        description=(
            "List all available courts in CourtListener. Returns court IDs that can be "
            "used to filter searches. Also shows convenient shortcuts like 'scotus' for "
            "Supreme Court or 'ca9' for 9th Circuit."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="get_opinion_pdf",
        description=(
            "Get the PDF URL for a court opinion, and optionally download it. "
            "Not all opinions have PDFs available. Returns the direct PDF URL "
            "which can be used to download the original court document."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "opinion_id": {
                    "type": "integer",
                    "description": "The opinion ID from a search result",
                },
                "save_path": {
                    "type": "string",
                    "description": "Optional file path to save the PDF (e.g., '/tmp/opinion.pdf')",
                },
            },
            "required": ["opinion_id"],
        },
    ),
]
