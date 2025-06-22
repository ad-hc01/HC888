# -*- coding: utf-8 -*-
# 本檔案負責查詢即時天氣資訊，來自 OpenWeatherMap API，若無金鑰則顯示預設訊息

import os
from typing import Optional

import httpx

DEFAULT_MESSAGE = "🌦️ 天氣查詢功能還在努力中～稍後就能使用囉！"
ERROR_MESSAGE = "⚠️ 天氣查詢失敗，請稍後再試或確認地點是否正確"

def get_weather_by_location(text: str) -> str:
    """
    查詢即時天氣資訊，使用 OpenWeatherMap API。
    :param text: 使用者輸入，如「台北天氣」
    :return: 格式化後的天氣資訊或錯誤提示
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return DEFAULT_MESSAGE

    # 擷取地點文字
    location = text.replace("天氣", "").replace("的", "").strip()
    if not location:
        return "❌ 請提供查詢地點，例如「台北天氣」。"

    try:
        url = (
            "http://api.openweathermap.org/data/2.5/weather"
            f"?q={location}&appid={api_key}"
            "&lang=zh_tw&units=metric"
        )
        resp = httpx.get(url, timeout=5.0)
        data = resp.json()

        if resp.status_code != 200 or "weather" not in data:
            return f"❌ 找不到 {location} 的天氣資訊"

        name = data.get("name")
        desc = data["weather"][0].get("description")
        temp = data.get("main", {}).get("temp")
        humidity = data.get("main", {}).get("humidity")

        return (
            f"📍 {name} 現在天氣：{desc}，"
            f"氣溫 {temp}°C，濕度 {humidity}%"
        )
    except httpx.RequestError as e:
        print(f"[get_weather_by_location] Request error: {e}")
    except Exception as e:
        print(f"[get_weather_by_location] Unexpected error: {e}")

    return ERROR_MESSAGE
