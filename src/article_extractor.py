import requests
from bs4 import BeautifulSoup


def extract_article_from_url(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) >= 40:
            paragraphs.append(text)

    article_text = "\n\n".join(paragraphs)

    if not article_text.strip():
        raise ValueError("No article text could be extracted from this URL.")

    return article_text[:18000]