# -*- coding: utf-8 -*-
# 本檔案使用 YouTube Data API v3 搜尋影片，並回傳純文字格式結果連結

import os
import requests

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_flex(query: str) -> str:
    if not YOUTUBE_API_KEY:
        return "❌ 尚未設定 YOUTUBE_API_KEY，請先設定才能使用 YouTube 搜尋功能。"

    try:
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY
        }

        response = requests.get(search_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            return f"❌ 找不到與「{query}」相關的影片"

        video = data["items"][0]
        vid = video["id"]["videoId"]
        snippet = video["snippet"]
        title = snippet["title"]
        channel = snippet["channelTitle"]
        video_url = f"https://www.youtube.com/watch?v={vid}"

        return f"🎬 {title}\n📺 頻道：{channel}\n🔗 {video_url}"

    except Exception as e:
        return f"⚠️ 搜尋失敗：{e}"
