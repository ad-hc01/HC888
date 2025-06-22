# -*- coding: utf-8 -*-
# 本檔案為 GPT 回答失敗時的搜尋補充模組，模擬 Google/Bing 搜尋結果回應格式。

def search_web_fallback(query: str) -> str:
    """
    模擬搜尋引擎回應，當 GPT 回答不了時提供補充建議。
    未來可改接 Google API、Bing Search API 或 Wikipedia。
    """
    fake_results = [
        {
            "title": f"{query} - 維基百科",
            "url": f"https://zh.wikipedia.org/wiki/{query.replace(' ', '_')}"
        },
        {
            "title": f"{query} 的說明與解析 - 知乎",
            "url": f"https://www.zhihu.com/search?q={query}"
        },
        {
            "title": f"{query} 的最新解法與教學 - Google 搜尋",
            "url": f"https://www.google.com/search?q={query}"
        }
    ]

    reply = "📚 我幫你查了一些資訊：\n"
    for item in fake_results:
        reply += f"🔸 {item['title']}\n{item['url']}\n"

    return reply
