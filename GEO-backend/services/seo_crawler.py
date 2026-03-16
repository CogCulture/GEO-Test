import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging

logger = logging.getLogger(__name__)

# Native fetching matching claude-seo behavior
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GEO-SEO/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

MAX_SUPPORTED_PAGES = 30

def fetch_page(url: str, timeout: int = 30) -> dict:
    """Fetch HTML content natively without Bright Data."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Only process HTML
        if 'text/html' not in response.headers.get('content-type', ''):
            return {"url": url, "html": None, "error": "Not an HTML page"}
            
        return {"url": response.url, "html": response.text, "error": None}
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return {"url": url, "html": None, "error": str(e)}

def extract_links(html: str, base_url: str, domain: str) -> list:
    """Extract internal links from HTML."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Skip fragments/mailto/tel
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
            
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Internal links only
        if parsed.netloc == domain or not parsed.netloc:
            # Strip fragments for deduplication
            clean_url = full_url.split('#')[0]
            links.append(clean_url)
            
    return list(set(links))

def crawl_site(start_url: str, max_pages: int = MAX_SUPPORTED_PAGES) -> list:
    """
    Crawls a website up to a hard limit of max_pages (default 30).
    Returns a list of dictionaries with 'url' and 'html' keys.
    """
    domain = urlparse(start_url).netloc
    if not domain:
        start_url = f"https://{start_url}"
        domain = urlparse(start_url).netloc

    visited = set()
    queue = [start_url]
    results = []

    while queue and len(results) < max_pages:
        url = queue.pop(0)
        
        if url in visited:
            continue
            
        visited.add(url)
        logger.info(f"Crawling {url} ({len(results)+1}/{max_pages})")
        
        page_data = fetch_page(url)
        if page_data["html"]:
            results.append({
                "url": page_data["url"],
                "html": page_data["html"]
            })
            
            # Add new internal links to the queue
            internal_links = extract_links(page_data["html"], page_data["url"], domain)
            for link in internal_links:
                if link not in visited and link not in queue:
                    queue.append(link)
                    
        time.sleep(0.5) # Gentle crawling

    return results
