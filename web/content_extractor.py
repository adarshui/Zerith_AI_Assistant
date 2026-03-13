"""
Zerith AI — Content Extractor
Extract main content from web pages and summarize with LLM.
"""

from utils.logger import log


def extract_content(url: str) -> str:
    """
    Extract and clean the main content from a URL.
    Strips navigation, ads, and boilerplate.
    """
    from web.scraper import scrape_page

    log.info(f"[cyan]Extracting content from:[/cyan] {url}")
    raw_text = scrape_page(url)

    if raw_text.startswith("Scraping failed"):
        return raw_text

    # Basic content cleaning — remove short lines (likely nav/ads)
    lines = raw_text.splitlines()
    content_lines = [line for line in lines if len(line) > 30]
    text = "\n".join(content_lines)

    log.info(f"Extracted {len(text)} characters of content")
    return text[:3000]


def summarize_content(url: str) -> str:
    """
    Extract content from a URL and summarize it using the LLM.
    """
    content = extract_content(url)

    if content.startswith("Scraping failed") or len(content) < 50:
        return f"Not enough content to summarize from {url}"

    try:
        from core.brain import Brain
        brain = Brain()
        prompt = f"Summarize the following web page content in 3-5 bullet points:\n\n{content}"
        result = brain.chat(prompt)
        log.info("Content summarized successfully")
        return result
    except Exception as e:
        log.warning(f"Summarization failed: {e}")
        return f"Content extracted but summarization failed: {e}\n\nRaw content:\n{content[:1000]}"


# Handler map for router registration
HANDLERS = {
    "extract_content": extract_content,
    "summarize_content": summarize_content,
}
