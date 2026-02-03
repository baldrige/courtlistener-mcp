# CourtListener MCP Server

An MCP (Model Context Protocol) server for searching court opinions and legal citations via the [CourtListener](https://www.courtlistener.com/) API.

## Installation

```bash
cd ~/Research/courtlistener-mcp
pip install -e .
```

## Configuration

Set your CourtListener API token:

```bash
export COURTLISTENER_API_TOKEN=your_token_here
```

Get a token at: https://www.courtlistener.com/profile/api/

## Claude Code Integration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "courtlistener": {
      "command": "python",
      "args": ["-m", "courtlistener_mcp.server"],
      "cwd": "/Users/49753464/Research/courtlistener-mcp",
      "env": {
        "COURTLISTENER_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Available Tools

### search_opinions
Search for court opinions by keyword, topic, or legal doctrine.

**Parameters:**
- `query` (required): Search terms
- `court`: Court ID or shortcut (e.g., "scotus", "ca9")
- `date_after`: Filter by date (YYYY-MM-DD)
- `date_before`: Filter by date (YYYY-MM-DD)
- `limit`: Max results (default: 20)

### get_opinion
Fetch the full text of a court opinion by ID.

**Parameters:**
- `opinion_id` (required): Opinion ID from search results

### lookup_citation
Resolve a legal citation to find the case.

**Parameters:**
- `citation` (required): Legal citation (e.g., "410 U.S. 113")

### list_courts
List available courts and shortcuts.

## Court Shortcuts

| Shortcut | Court |
|----------|-------|
| scotus | Supreme Court |
| ca1-ca11 | Circuit Courts |
| cadc | DC Circuit |
| cafc | Federal Circuit |

## Example Queries

After setup, you can ask Claude Code:

- "Search for Supreme Court cases about First Amendment and social media"
- "Look up the full text of Roe v. Wade (410 U.S. 113)"
- "Find 9th Circuit cases about qualified immunity since 2020"
- "What cases cite Brown v. Board of Education?"
