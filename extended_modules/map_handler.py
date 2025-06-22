# -*- coding: utf-8 -*-
# 本檔案為地圖查詢模組，使用 Google Maps 靜態圖 API 回傳純文字圖片連結，供 LINE 使用者查詢地點或附近資訊

import os
import urllib.parse

GOOGLE_MAPS_STATIC_URL = "https://maps.googleapis.com/maps/api/staticmap"

def generate_map_image(query_text: str) -> str:
    """
    根據地點名稱 query_text 傳回一段文字，內含 Google Maps 靜態圖連結。
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "❌ 尚未設定 GOOGLE_MAPS_API_KEY，無法查詢地圖。"

    try:
        params = {
            "center": query_text,
            "zoom": 15,
            "size": "640x480",
            "maptype": "roadmap",
            "markers": f"color:red|label:X|{query_text}",
            "key": api_key
        }

        query_string = urllib.parse.urlencode(params)
        image_url = f"{GOOGLE_MAPS_STATIC_URL}?{query_string}"
        return f"🗺 地圖：{query_text}\n{image_url}"
    except Exception as e:
        return f"⚠️ 地圖查詢失敗：{e}"
