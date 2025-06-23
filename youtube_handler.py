# -*- coding: utf-8 -*-
# 本檔案負責處理使用者的音樂、MV、影片搜尋需求，
# 並以純文字方式回傳 YouTube 連結（使用真實 API）

import os
import requests
from linebot.v3.messaging import TextMessage as V3TextMessage

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_card(query: str) -> V3TextMessage:
    if not YOUTUBE_API_KEY:
        return V3TextMessage(text="❌ 尚未設定 YOUTUBE_API_KEY，請先設定才能使用 YouTube 搜尋功能。")

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "order": "relevance",
            "key": YOUTUBE_API_KEY
        }

        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        if not data.get("items"):
            return V3TextMessage(text=f"❌ 找不到與「{query}」相關的影片")

        item = data["items"][0]
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        return V3TextMessage(text=f"🎬 {title}\n{url}")

    except Exception as e:
        return V3TextMessage(text=f"⚠️ YouTube 搜尋失敗：{e}")
