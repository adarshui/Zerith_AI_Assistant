"""
Zerith AI — Web Scraper
Scrape web pages using requests + BeautifulSoup (with Playwright fallback for JS pages).
"""

from utils.logger import log


def scrape_page(url: str, use_playwright: bool = False) -> str:
    """
    Scrape a web page and return its text content.
    Uses requests+BS4 by default; set use_playwright=True for JS-heavy pages.
    """
    log.info(f"[cyan]Scraping:[/cyan] {url}")

    if use_playwright:
        return _scrape_with_playwright(url)
    return _scrape_with_requests(url)


def _scrape_with_requests(url: str) -> str:
    """Scrape using requests + BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Zerith-AI/1.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        log.info(f"Scraped {len(text)} characters from {url}")
        return text[:5000]  # Limit output size

    except Exception as e:
        log.warning(f"Requests scraping failed: {e}")
        return f"Scraping failed: {e}"


def _scrape_with_playwright(url: str) -> str:
    """Scrape using Playwright (handles JavaScript-rendered pages)."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # Wait for content to load
            page.wait_for_timeout(2000)
            text = page.inner_text("body")
            browser.close()

        log.info(f"Playwright scraped {len(text)} characters from {url}")
        return text[:5000]

    except Exception as e:
        log.warning(f"Playwright scraping failed: {e}")
        return f"Playwright scraping failed: {e}"


def get_page_title(url: str) -> str:
    """Get the title of a web page."""
    try:
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title else "No title"
        return title.strip()
    except Exception as e:
        return f"Could not get title: {e}"


# Handler map for router registration
HANDLERS = {
    "scrape_page": scrape_page,
    "get_page_title": get_page_title,
}
