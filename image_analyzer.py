# -*- coding: utf-8 -*-
# 本模組負責圖片分析：將 LINE 傳來的圖片下載並以 base64 傳給 GPT-4o 分析，並回傳 LINE 訊息物件

import base64
import requests
from openai import OpenAI, OpenAIError
from linebot.v3.messaging import TextMessage as V3TextMessage
from linebot.v3.messaging import MessagingApi

client = OpenAI()

def analyze_image_with_gpt(message_id: str, api: MessagingApi, user_name: str = None, ai_name: str = "HC", style: str = "正式風") -> V3TextMessage:
    """
    從 LINE 下載圖片，轉 base64，再呼叫 GPT-4o 進行圖像內容分析。
    回傳 V3TextMessage 供主程式直接回覆。
    """
    try:
        print(f"[DEBUG] analyze_image_with_gpt called for message_id: {message_id}")
        # 從 LINE 下載圖片
        headers = {"Authorization": f"Bearer {api.api_client.configuration.access_token}"}
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        resp = requests.get(image_url, headers=headers, timeout=10)

        if resp.status_code != 200:
            err = f"❌ 圖片下載失敗（HTTP {resp.status_code}）"
            print(f"[ERROR] analyze_image_with_gpt: {err}")
            return V3TextMessage(text=err)

        image_data = resp.content
        if not image_data or len(image_data) < 500:
            err = "❌ 取得的圖片資料過小，請確認上傳了清晰的圖片。"
            print(f"[ERROR] analyze_image_with_gpt: {err}")
            return V3TextMessage(text=err)

        # 編碼至 base64 data URL
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:{content_type};base64,{base64_data}"
        print("[DEBUG] Image downloaded and encoded to base64")

        # 組裝 GPT-4o 訊息
        system_prompt = f"你是名叫 {ai_name} 的圖像分析助手，請用「{style}」風格幫助使用者解讀以下圖片內容。"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "請幫我分析這張圖片的內容。"},
                {"type": "image_url", "image_url": data_url}
            ]}
        ]

        # 呼叫 GPT-4o
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.6,
            max_tokens=600
        )
        text = result.choices[0].message.content.strip()
        print("[DEBUG] GPT-4o image analysis succeeded")
        return V3TextMessage(text=text)

    except OpenAIError as e:
        err = f"❌ GPT 圖像分析失敗：{e}"
        print(f"[ERROR] analyze_image_with_gpt OpenAIError: {e}")
        return V3TextMessage(text=err)
    except Exception as e:
        err = f"⚠️ 圖像分析異常：{type(e).__name__} - {e}"
        print(f"[ERROR] analyze_image_with_gpt Unexpected: {e}")
        return V3TextMessage(text=err)
