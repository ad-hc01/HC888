# -*- coding: utf-8 -*-
# 本檔案為 GPT 回答失敗時的搜尋補充模組

from typing import List

def search_web_fallback(query: str) -> str:
    """
    模擬搜尋引擎回應，當 GPT 回答不了時提供補充建議。
    未來可改接 Google API、Bing Search API 或 Wikipedia 等實際搜尋服務。
    :param query: 使用者查詢關鍵字
    :return: 組好的文字回覆
    """
    sources: List[dict] = [
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
    lines = ["📚 我幫你查了一些資訊："]
    for src in sources:
        lines.append(f"🔸 {src['title']}\n{src['url']}")
    return "\n".join(lines)
