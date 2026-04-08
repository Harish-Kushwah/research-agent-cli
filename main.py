import requests
from bs4 import BeautifulSoup
import ollama

from duckduckgo_search import DDGS


def _message_field(chunk, field_name):
    """Support both dict-style and object-style Ollama SDK responses."""
    if isinstance(chunk, dict):
        return chunk.get("message", {}).get(field_name, "")

    message = getattr(chunk, "message", None)
    if message is None:
        return ""

    return getattr(message, field_name, "")

def search_web(query):
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            results.append(r['href'])

    print(results)
    return results

# def search_web(query):
#     url = f"https://duckduckgo.com/html/?q={query}"
#     headers = {"User-Agent": "Mozilla/5.0"}
#     res = requests.get(url, headers=headers)
#     soup = BeautifulSoup(res.text, "html.parser")
#     results = []
#     for a in soup.select(".result__a")[:5]:
#         results.append(a.get("href"))

#     print(results)
#     return results


def scrape_page(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return " ".join(paragraphs[:20])  # limit content
    except:
        return ""


def summarize_with_ollama(content):
    prompt = f"""
    You are a UI/UX expert.

    From the content below, extract:
    1. Latest UI trends
    2. New tools/libraries
    3. Real-world examples
    4. Key takeaways

    Keep it short, structured, and in bullet points.

    Content:
    {content[:4000]}
    """

    response = ollama.chat(
        model="qwen3.5:4b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']


def summarize_with_streaming(content):
    prompt = f"""
    Give latest UI/UX trends in bullet points from below content:

    {content[:3000]}
    """

    stream = ollama.chat(
        model="qwen3.5:4b",
        messages=[{"role": "user", "content": prompt}],
        think=True,
        stream=True   # 🔥 IMPORTANT
    )

    full_response = ""
    full_thinking = ""
    in_thinking = False

    for chunk in stream:
        thinking_token = _message_field(chunk, "thinking")
        content_token = _message_field(chunk, "content")

        if thinking_token:
            if not in_thinking:
                print("Thinking:\n", end="", flush=True)
                in_thinking = True
            print(thinking_token, end="", flush=True)
            full_thinking += thinking_token
        elif content_token:
            if in_thinking:
                print("\n\nAnswer:\n", end="", flush=True)
                in_thinking = False
            print(content_token, end="", flush=True)   # 👈 REAL-TIME PRINT
            full_response += content_token

    return full_response

def ui_news_agent(query):
    urls = search_web(query)
    print(urls)
    full_content = ""
    for url in urls:
        full_content += scrape_page(url)

    return full_content
    # return summarize_with_streaming(full_content)


# Run
# print(ui_news_agent("latest UI UX trends 2026"))
print(summarize_with_streaming("latest UI UX trends 2026"))
