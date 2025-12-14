import json

import requests
from bs4 import BeautifulSoup

def create_hf_papers_json_feed(url, length=None):
    """
    https://huggingface.co/papersの論文情報を取得し、JSON Feed形式で返す。
    Refefference: https://github.com/capjamesg/hugging-face-papers-rss

    Args:
        url: Hugging Face PapersのURL (例: https://huggingface.co/papers/trending)。
        length: 取得する論文数の上限。Noneで制限なし。

    Returns:
        JSON Feed形式の辞書。

    """
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")

    h3s = soup.find_all("h3")
    if length is not None:
        h3s = h3s[:length]

    papers = []


    def extract_abstraction(url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        abstract = soup.find("div", {"class": "pb-8 pr-4 md:pr-16"}).text

        time_element = soup.find("time")
        datetime_str = time_element.get("datetime") if time_element else None
        if datetime_str and not datetime_str.endswith("Z"):
            datetime_str = f"{datetime_str}Z"

        if abstract.startswith("Abstract\n"):
            abstract = abstract[len("Abstract\n") :]
        abstract = abstract.replace("\n", " ")
        return abstract, datetime_str


    for h3 in h3s:
        a = h3.find("a")
        title = a.text
        link = a["href"]
        url = f"https://huggingface.co{link}"
        try:
            abstract, datetime_str = extract_abstraction(url)
        except Exception as e:
            print(f"Failed to extract abstract for {url}: {e}")
            abstract, datetime_str = "", None

        papers.append({"title": title, "url": url, "abstract": abstract, "date_published": datetime_str})

    feed = {
        "version": "https://jsonfeed.org/version/1",
        "title": "Hugging Face Papers",
        "home_page_url": url,
        "feed_url": "https://example.org/feed.json",
        "items": sorted(
            [
                {
                    "id": p["url"],
                    "title": p["title"].strip(),
                    "content_text": p["abstract"].strip(),
                    "url": p["url"],
                    **({"date_published": p["date_published"]} if p["date_published"] else {}),
                }
                for p in papers
            ],
            key=lambda x: x.get("date_published", ""),
            reverse=True,
        ),
    }

    return feed