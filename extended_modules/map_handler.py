# -*- coding: utf-8 -*-
# 本檔案為地圖圖片處理模組，使用 Google Maps Static API 生成地圖快照

import os
import urllib.parse
from linebot.v3.messaging import ImageMessage as V3ImageMessage, TextMessage as V3TextMessage
import requests

def generate_map_image(text: str):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return V3TextMessage(text="❌ 尚未設定 Google Maps API 金鑰，請先設定才能查地圖喔！")

    # 解析地點
    if "地圖" in text:
        location = text.split("地圖")[-1].strip()
    else:
        location = text.strip()

    if not location or location.lower() in ["xx", "圖片", "地圖", "x", "?"]:
        return V3TextMessage(text="❌ 抱歉，我無法判斷你想查哪裡的地圖，請再輸入具體地點 🙏")

    encoded_location = urllib.parse.quote(location)
    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={encoded_location}&zoom=15&size=600x400&maptype=roadmap&key={api_key}&markers=color:red%7C{encoded_location}"

    # 預先請求圖片確認 URL 可用
    try:
        r = requests.get(map_url, timeout=5)
        if r.status_code != 200 or r.headers.get("Content-Type", "").lower() != "image/png":
            return V3TextMessage(text=f"⚠️ 查不到「{location}」的地圖，請再確認地名是否正確")
    except Exception as e:
        return V3TextMessage(text=f"⚠️ 地圖生成失敗，可能是金鑰或地點問題：{e}")

    return V3ImageMessage(
        original_content_url=map_url,
        preview_image_url=map_url
    )
