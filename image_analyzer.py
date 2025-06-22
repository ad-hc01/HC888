# -*- coding: utf-8 -*-
# 本檔案負責圖片分析功能，使用 GPT-4o 的多模態能力處理 LINE 傳來的圖片內容（以 base64 傳輸）

import openai
import base64
from io import BytesIO

def analyze_image_with_gpt(message_id: str, line_bot_api, user_name: str = None, ai_name: str = "AI", style: str = "正式風") -> str:
    """
    使用 GPT-4o 分析 LINE 傳來的圖片，透過 base64 轉換內容，提升穩定性與準確率。
    """
    try:
        # 從 LINE 取得圖片內容並轉成 base64
        message_content = line_bot_api.get_message_content(message_id)
        image_bytes = BytesIO()
        for chunk in message_content.iter_content():
            image_bytes.write(chunk)
        base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

        # 準備提示語
        system_prompt = "你是一位圖像分析導師，請幫助使用者詳細描述圖片內容，並提供延伸觀察。"
        style_prefix = {
            "可愛風": "嗨嗨～這是我看到的唷：",
            "正式風": "您好，這是您圖片的分析結果：",
            "搞笑風": "哇～這張圖也太有趣了吧，我來說說："
        }.get(style, "")

        # 呼叫 GPT-4o Vision
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "請分析這張圖片，說明內容並給予觀察建議"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ]
        )

        result = response.choices[0].message.content
        return f"{style_prefix}{result.strip()}"
    except Exception as e:
        return "這張圖片無法分析，可能格式錯誤或內容不清晰唷。"
