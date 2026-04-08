from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from ui_news_agent.utils import browser_user_agent

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


def search_web(query: str, max_results: int = 5) -> list[str]:
    if DDGS is not None:
        try:
            results: list[str] = []
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=max_results):
                    href = item.get("href") or item.get("url")
                    if href and href not in results:
                        results.append(href)
            if results:
                print(f"Found {len(results)} results via DDGS")
                return results
        except Exception as exc:
            print(f"DDGS search failed: {exc}")

    results = _search_duckduckgo_html(query, max_results=max_results)
    if results:
        print(f"Found {len(results)} results via DuckDuckGo HTML")
        return results

    results = _search_google_html(query, max_results=max_results)
    if results:
        print(f"Found {len(results)} results via Google HTML")
        return results

    print("No results found from any search provider.")
    return []


def scrape_page(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": browser_user_agent()},
            timeout=10,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return " ".join(p for p in paragraphs if p)[:5000]
    except Exception as exc:
        print(f"Failed to scrape {url}: {exc}")
        return ""


def _search_duckduckgo_html(query: str, max_results: int = 5) -> list[str]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": browser_user_agent()},
            timeout=10,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        results: list[str] = []
        for anchor in soup.select(".result__a"):
            href = anchor.get("href")
            if href and href not in results:
                results.append(href)
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        print(f"DuckDuckGo HTML search failed: {exc}")
        return []


def _search_google_html(query: str, max_results: int = 5) -> list[str]:
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": browser_user_agent()},
            timeout=10,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        results: list[str] = []
        for anchor in soup.select("a"):
            href = anchor.get("href", "")
            if href.startswith("/url?q="):
                clean_url = href.split("/url?q=", 1)[1].split("&", 1)[0]
                if clean_url.startswith("http") and clean_url not in results:
                    results.append(clean_url)
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        print(f"Google HTML search failed: {exc}")
        return []
