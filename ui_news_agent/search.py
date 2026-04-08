from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from ui_news_agent.utils import browser_user_agent

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


class SearchProviderError(RuntimeError):
    pass


class SearchConnectivityError(SearchProviderError):
    pass


class SearchEmptyResultError(SearchProviderError):
    pass


def search_web(query: str, max_results: int = 5) -> list[str]:
    provider_errors: list[str] = []
    connectivity_failures = 0

    providers = [
        ("ddgs", lambda: _search_with_ddgs(query, max_results=max_results)),
        (
            "duckduckgo_html",
            lambda: _search_duckduckgo_html(query, max_results=max_results),
        ),
        ("google_html", lambda: _search_google_html(query, max_results=max_results)),
    ]

    for provider_name, provider in providers:
        try:
            results = provider()
            if results:
                print(f"Found {len(results)} results via {provider_name}")
                return results
            provider_errors.append(f"{provider_name}: returned 0 results")
        except SearchConnectivityError as exc:
            connectivity_failures += 1
            provider_errors.append(f"{provider_name}: network blocked or unavailable ({exc})")
        except Exception as exc:
            provider_errors.append(f"{provider_name}: {exc}")

    print("No results found from any search provider.")
    for error in provider_errors:
        print(f"  - {error}")

    if connectivity_failures == len(providers):
        print("All search providers failed due to connectivity issues. Check firewall, proxy, VPN, antivirus, or corporate network rules.")

    return []


def _search_with_ddgs(query: str, max_results: int = 5) -> list[str]:
    if DDGS is None:
        raise SearchProviderError(
            "Package 'ddgs' is not installed. Run: pip install ddgs"
        )

    try:
        results: list[str] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                href = item.get("href") or item.get("url")
                if href and href not in results:
                    results.append(href)
        return results
    except Exception as exc:
        raise _normalize_search_error(exc) from exc



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
    response = _get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    results: list[str] = []
    for anchor in soup.select(".result__a"):
        href = anchor.get("href")
        if href and href not in results:
            results.append(href)
        if len(results) >= max_results:
            break
    return results



def _search_google_html(query: str, max_results: int = 5) -> list[str]:
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en"
    response = _get(url)
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



def _get(url: str) -> requests.Response:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": browser_user_agent()},
            timeout=10,
        )
        response.raise_for_status()
        return response
    except Exception as exc:
        raise _normalize_search_error(exc) from exc



def _normalize_search_error(exc: Exception) -> SearchProviderError:
    message = str(exc)
    connectivity_markers = [
        "WinError 10013",
        "Failed to establish a new connection",
        "Max retries exceeded",
        "ConnectError",
        "ConnectionError",
        "timed out",
        "Temporary failure in name resolution",
    ]

    if any(marker in message for marker in connectivity_markers):
        return SearchConnectivityError(message)

    if "returned 0 results" in message:
        return SearchEmptyResultError(message)

    return SearchProviderError(message)
