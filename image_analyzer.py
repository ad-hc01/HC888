# -*- coding: utf-8 -*-
# 本檔案負責圖片分析功能，使用 GPT-4o 的多模態能力處理 LINE 傳來的圖片內容

import base64
from io import BytesIO
from openai import OpenAI
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging.models import GetMessageContentRequest  # 修正位址

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

def analyze_image_with_gpt(
    message_id: str,
    api: MessagingApi,
    user_name: str | None = None,
    ai_name: str = "AI",
    style: str = "正式風"
) -> str:
    """
    使用 GPT-4o 分析 LINE 傳來的圖片。
    :param api: 已初始化的 MessagingApi 實例
    :param message_id: LINE 圖片訊息 ID
    :param user_name: 使用者顯示名稱（可 None）
    :param ai_name: AI 名稱
    :param style: 回答風格
    """
    # 1. 下載圖片內容
    try:
        req = GetMessageContentRequest(message_id=message_id)
        resp = api.get_message_content(req)
        buf = BytesIO()
        for chunk in resp.iter_bytes():
            buf.write(chunk)
        img_data = buf.getvalue()
    except Exception:
        return "❌ 取得圖片內容失敗，請稍後再試。"

    # 2. 轉 base64
    b64 = base64.b64encode(img_data).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64}"

    # 3. 組裝系統提示
    style_prefix = f""
    system_prompt = (
        f"你是一位具備圖像理解能力的 AI，名稱是「{ai_name}」。"
        "請根據使用者傳來的圖片進行分析，說明主要物體或場景，並提供觀察建議。"
    )

    # 4. 建立多模態訊息
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
