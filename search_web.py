# -*- coding: utf-8 -*-
# 本模組用於進行即時網路搜尋（Bing + Google + Wikipedia）以補足 GPT 回答不足的情境

import requests
from bs4 import BeautifulSoup

def search_web_bing(query: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.bing.com/search?q={query}"
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        snippets = soup.select("li.b_algo p")
        texts = [s.get_text() for s in snippets if s.get_text()]
        return "\n".join(texts[:3]) if texts else "❓ 找不到相關資訊。"
    except Exception:
        return "❓ Bing 搜尋失敗。"

def search_web_google(query: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        snippets = soup.select("div.BNeawe.s3v9rd.AP7Wnd")
        texts = [s.get_text() for s in snippets if s.get_text()]
        return "\n".join(texts[:3]) if texts else "❓ Google 沒找到資訊。"
    except Exception:
        return "❓ Google 搜尋失敗。"

def search_wikipedia(query: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://zh.wikipedia.org/wiki/{query}"
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        para = soup.select("p")
        for p in para:
            text = p.get_text(strip=True)
            if len(text) > 30:
                return text
        return "❓ 維基百科中未找到有用內容。"
    except Exception:
        return "❓ 維基百科搜尋失敗。"

def search_all_sources(query: str) -> str:
    sources = [
        search_web_bing(query),
        search_web_google(query),
        search_wikipedia(query.replace(" ", "_"))
    ]
    combined = "\n\n".join([s for s in sources if s and "❓" not in s])
    return combined if combined else "❓ 無法從公開資料中取得答案。"
