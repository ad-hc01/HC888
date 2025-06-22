# -*- coding: utf-8 -*-
# 本檔案負責處理使用者圖片生成請求，透過 DALL·E 3 並回傳給 LINE 用戶

from openai import OpenAI, OpenAIError
from linebot.v3.messaging import TextMessage as V3TextMessage, ImageMessage as V3ImageMessage

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

# 敏感詞過濾（簡化版）
SENSITIVE_KEYWORDS = ["裸體", "色情", "暴力", "血腥", "自殺", "仇恨"]

def is_sensitive(prompt: str) -> bool:
    return any(kw in prompt for kw in SENSITIVE_KEYWORDS)

def generate_image_message(prompt: str):
    """
    根據輸入提示詞生成圖片，並以 LINE V3 ImageMessage 格式回傳。
    若為敏感詞則回傳警告文字訊息。
    """
    if is_sensitive(prompt):
        return V3TextMessage(text="❌ 這類圖片無法提供，請嘗試其他主題～")

    try:
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            response_format="url"
        )
        image_url = resp.data[0].url
        return V3ImageMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    except OpenAIError as e:
        print(f"[generate_image_message] OpenAI API error: {e}")
    except Exception as e:
        print(f"[generate_image_message] Unexpected error: {e}")

    return V3TextMessage(text="⚠️ 目前無法生成圖片，請稍後再試。")
