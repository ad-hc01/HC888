# -*- coding: utf-8 -*-
# 地圖查詢模組（LINE V3），使用 Google Maps 靜態圖 API 回傳地圖圖片

import os
import urllib.parse
from linebot.v3.messaging import ImageMessage as V3ImageMessage, TextMessage as V3TextMessage

GOOGLE_MAPS_STATIC_URL = "https://maps.googleapis.com/maps/api/staticmap"

def generate_map_image(query_text: str):
    """
    根據地點名稱生成地圖圖片，回傳 V3ImageMessage 或錯誤提示文字。
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return V3TextMessage(text="❌ 未設定 Google Maps API 金鑰，無法查詢地圖。")

    params = {
        "center": query_text,
        "zoom": 15,
        "size": "640x480",
        "maptype": "roadmap",
        "markers": f"color:red|label:X|{query_text}",
        "key": api_key
    }
    url = f"{GOOGLE_MAPS_STATIC_URL}?{urllib.parse.urlencode(params)}"
    return V3ImageMessage(
        original_content_url=url,
        preview_image_url=url
    )
