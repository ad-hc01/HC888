# -*- coding: utf-8 -*-
# 本模組負責圖片分析：將 LINE 傳來的圖片下載並以 base64 傳給 GPT 分析
# image_analyzer.py → 專責「圖片辨識」（GPT-4o base64）
# image_generator.py → 專責「主題生成」
# image_generator_style.py → 專責「風格轉換」

import base64
import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI
from linebot.v3.messaging.models import TextMessage as V3TextMessage
from linebot.v3.messaging import MessagingApi

# 嘗試 import pytesseract，並設定執行檔路徑
try:
    import pytesseract
    import os
    TESSERACT_CMD = "/usr/bin/tesseract"
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    else:
        pytesseract = None
except ImportError:
    pytesseract = None

client = OpenAI()

def analyze_image_with_gpt(message_id: str, api: MessagingApi, user_name=None, ai_name="HC", style="正式風") -> list:
    messages = []
    try:
        # 從 LINE 下載圖片
        headers = {
            "Authorization": f"Bearer {api.api_client.configuration.access_token}"
        }
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        response = requests.get(image_url, headers=headers)

        if response.status_code != 200:
            return [V3TextMessage(text=f"❌ 圖片下載失敗（錯誤碼 {response.status_code}），請再試一次。")]

        image_data = response.content
        if not image_data or len(image_data) < 500:
            return [V3TextMessage(text="❌ 圖片內容異常，請確認你上傳的是清晰的圖片格式（非貼圖、非空白）。")]

        # base64 圖片準備給 GPT
        content_type = response.headers.get("Content-Type", "image/jpeg")
        base64_data = base64.b64encode(image_data).decode("utf-8")
        image_data_url = f"data:{content_type};base64,{base64_data}"

        # 傳給 GPT-4o 處理主題
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"你是名叫 {ai_name} 的圖像分析助手，請用「{style}」風格幫助使用者解讀圖片內容。"},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ],
            temperature=0.6,
            max_tokens=600
        )

        gpt_result = gpt_response.choices[0].message.content.strip()
        messages.append(V3TextMessage(text=f"📷 已分析圖片內容如下：\n{gpt_result}"))

        # OCR 分析（有 pytesseract 且 tesseract 執行檔存在才執行）
        if pytesseract:
            try:
                ocr_image = Image.open(BytesIO(image_data))
                ocr_result = pytesseract.image_to_string(ocr_image, lang='eng+chi_tra').strip()
                if ocr_result:
                    messages.append(V3TextMessage(text=f"📝 圖中文字內容：\n{ocr_result}"))
            except Exception as e:
                messages.append(V3TextMessage(text=f"⚠️ 圖像文字辨識失敗：{e}"))
        else:
            messages.append(V3TextMessage(text="⚠️ OCR 功能目前不可用（缺少 pytesseract 或 tesseract 執行檔）。"))

    except Exception as e:
        messages.append(V3TextMessage(text=f"⚠️ 無法分析圖片，發生錯誤：{e}"))

    return messages
