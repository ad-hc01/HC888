# -*- coding: utf-8 -*-
# 本檔案負責查詢即時天氣資訊，來自 OpenWeatherMap API，若無金鑰則顯示預設訊息

import os
import requests

def get_weather_by_location(text: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "🌦️ 天氣查詢功能還在努力中～稍後就能使用囉！"

    location = (
        text.replace("天氣", "")
            .replace("的", "")
            .replace("如何", "")
            .replace("怎麼樣", "")
            .strip()
    )

    if not location:
        return "請提供要查詢天氣的地點名稱喔～"

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "lang": "zh_tw",
            "units": "metric"
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") != 200:
            return f"❌ 找不到「{location}」的天氣資訊"

        name = data.get("name", location)
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})

        desc = weather.get("description", "無資料")
        temp = main.get("temp", "?")
        humidity = main.get("humidity", "?")

        return f"📍 {name} 現在天氣：{desc}，氣溫 {temp}°C，濕度 {humidity}%"

    except requests.exceptions.Timeout:
        return "⚠️ 天氣伺服器回應超時，請稍後再試。"
    except requests.exceptions.RequestException as e:
        return f"⚠️ 天氣查詢錯誤：{e}"
    except Exception:
        return "⚠️ 天氣查詢失敗，請稍後再試或確認地點是否正確"
