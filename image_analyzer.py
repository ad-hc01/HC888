# -*- coding: utf-8 -*-
# 本模組負責圖片分析：將 LINE 傳來的圖片下載並以 base64 傳給 GPT 分析

import base64
import requests
from openai import OpenAI
from linebot.v3.messaging import MessagingApi

client = OpenAI()

def analyze_image_with_gpt(message_id: str, api: MessagingApi, user_name=None, ai_name="HC", style="正式風") -> str:
    try:
        # 從 LINE 下載圖片
        headers = {
            "Authorization": f"Bearer {api.api_client.configuration.access_token}"
        }
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        response = requests.get(image_url, headers=headers)

        if response.status_code != 200:
            return f"❌ 圖片下載失敗（錯誤碼 {response.status_code}），請再試一次。"

        image_data = response.content
        if not image_data or len(image_data) < 500:
            return "❌ 圖片內容異常，請確認你上傳的是清晰的圖片格式（非貼圖、非空白）。"

        # 判斷圖片格式
        content_type = response.headers.get("Content-Type", "image/jpeg")
        base64_data = base64.b64encode(image_data).decode("utf-8")
        image_data_url = f"data:{content_type};base64,{base64_data}"

        # 傳給 GPT-4o 處理
        messages = [
            {
                "role": "system",
                "content": f"你是名叫 {ai_name} 的圖像分析助手，請用「{style}」風格幫助使用者解讀圖片內容。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ]

        result = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.6,
            max_tokens=600
        )

        return result.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ 無法分析圖片，發生錯誤：{e}"
