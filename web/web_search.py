"""
Zerith AI — Web Search
Search the internet using DuckDuckGo (free, no API key needed).
"""

from utils.logger import log


def search(query: str, max_results: int = 5) -> str:
    """
    Search the web and return top results.
    Uses DuckDuckGo search (no API key required).
    """
    log.info(f"[cyan]Web search:[/cyan] {query}")

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return "No results found."

        output_lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("href", "")
            snippet = r.get("body", "")
            output_lines.append(f"{i}. {title}\n   {url}\n   {snippet}\n")

        result_text = "\n".join(output_lines)
        log.info(f"Found {len(results)} result(s)")
        return result_text

    except Exception as e:
        log.warning(f"Web search failed: {e}")
        return f"Web search failed: {e}"


def search_news(query: str, max_results: int = 5) -> str:
    """Search for recent news articles."""
    log.info(f"[cyan]News search:[/cyan] {query}")

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))

        if not results:
            return "No news found."

        output_lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            date = r.get("date", "")
            output_lines.append(f"{i}. [{date}] {title}\n   {url}\n")

        return "\n".join(output_lines)

    except Exception as e:
        log.warning(f"News search failed: {e}")
        return f"News search failed: {e}"


# Handler map for router registration
HANDLERS = {
    "search": search,
    "search_news": search_news,
}
