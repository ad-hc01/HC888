# -*- coding: utf-8 -*-
# 本檔案負責處理使用者圖片生成請求，透過 DALL·E 並回傳給 LINE 用戶

import os
import httpx
from openai import OpenAI
from linebot.v3.messaging import TextMessage as V3TextMessage, ImageMessage as V3ImageMessage

# 初始化 OpenAI 客戶端（使用新版 SDK）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client()
)

# 敏感詞過濾（簡化版）
SENSITIVE_KEYWORDS = ["裸體", "色情", "暴力", "血腥", "自殺", "仇恨"]

def is_sensitive(prompt):
    return any(kw in prompt for kw in SENSITIVE_KEYWORDS)

def generate_image_message(prompt: str):
    """
    根據輸入提示詞生成圖片，並以 LINE V3ImageMessage 格式回傳。
    若為敏感詞則回傳警告文字訊息。
    """
    if is_sensitive(prompt):
        return V3TextMessage(text="這類圖片無法提供，請嘗試其他主題～")

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url
        return V3ImageMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    except Exception as e:
        print(f"[Image Generation Error] {e}")
        return V3TextMessage(text="目前無法生成圖片，請稍後再試。")
