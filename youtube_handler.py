# -*- coding: utf-8 -*-
# 本檔案負責處理使用者的音樂、MV、影片搜尋需求，
# 並以純文字方式回傳 YouTube 連結

from urllib.parse import quote
from linebot.v3.messaging import TextMessage as V3TextMessage

def search_youtube_card(query: str):
    """
    接收影片名稱關鍵字 query，
    回傳第一筆預測影片的連結文字訊息（模擬版，不使用 API key）。
    """
    # 模擬搜尋影片（實務可接 YouTube Data API 取首筆結果）
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    return V3TextMessage(
        text=(
            f"📺 與「{query}」相關的影片：\n"
            f"{video_url}\n\n"
            f"※ 如要看更多結果，可點此搜尋：\n"
            f"https://www.youtube.com/results?search_query={quote(query)}"
        )
    )
