# -*- coding: utf-8 -*-
# 本檔案負責圖片分析功能，使用 GPT-4o 的多模態能力處理 LINE 傳來的圖片內容

import os
import base64
from io import BytesIO

import requests
from openai import OpenAI

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

# LINE 圖片內容 API
CONTENT_URL = "https://api-data.line.me/v2/bot/message/{message_id}/content"

def analyze_image_with_gpt(
    message_id: str,
    user_name: str | None = None,
    ai_name: str = "AI",
    style: str = "正式風"
) -> str:
    """
    使用 GPT-4o 分析 LINE 傳來的圖片。
    直接向 LINE 伺服器拉 binary，再轉 base64 給 GPT 多模態。
    """
    # 1. 下載圖片二進位
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return "❌ 未設定 LINE_CHANNEL_ACCESS_TOKEN，無法取得圖片。"
    url = CONTENT_URL.format(message_id=message_id)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        img_data = resp.content
    except Exception:
        return "❌ 取得圖片內容失敗，請稍後再試。"

    # 2. 轉 base64
    b64 = base64.b64encode(img_data).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"

    # 3. 系統提示
    style_prefix = f""
    system_prompt = (
        f"你是一位具備圖像理解能力的 AI，名稱是「{ai_name}」。"
        "請根據使用者傳來的圖片進行分析，說明主要物體或場景，並提供觀察建議。"
    )

    # 4. 組裝多模態訊息
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "請分析這張圖片，說明內容並給予觀察建議。"},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ]
        }
    ]

    # 5. 呼叫 GPT-4o
    try:
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()
        return f"{style_prefix}{result}"
    except Exception:
        return "⚠️ 圖片分析失敗，請確認格式或稍後再試。"
