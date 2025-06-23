# -*- coding: utf-8 -*-
# 本檔案負責處理使用者圖片生成請求，透過 DALL·E 3 並回傳給 LINE 用戶
# 已整合：敏感詞過濾 + 風格細化提示生成

from openai import OpenAI, OpenAIError
from linebot.v3.messaging import TextMessage as V3TextMessage, ImageMessage as V3ImageMessage
from prompt_enhancer import enhance_prompt_with_style

client = OpenAI()

SENSITIVE_KEYWORDS = ["裸體", "色情", "暴力", "血腥", "自殺", "仇恨"]

def is_sensitive(prompt: str) -> bool:
    return any(kw in prompt for kw in SENSITIVE_KEYWORDS)

def generate_image_message(text: str):
    """
    使用者輸入如：「幫我生成 洛可可風格的貓咪插畫」
    將風格與主題分離並注入提示，再送至 DALL·E 生成圖片
    """
    if is_sensitive(text):
        return V3TextMessage(text="❌ 這類圖片無法提供，請嘗試其他主題～")

    try:
        # 自動分離風格關鍵詞（若有）
        if "風格" in text and "生成" in text:
            parts = text.replace("幫我生成", "").replace("風格", "").strip().split("的", 1)
            style = parts[0].strip()
            prompt = parts[1].strip() if len(parts) > 1 else "a cool concept"
        else:
            style = ""
            prompt = text.strip()

        # 強化提示
        enhanced_prompt = enhance_prompt_with_style(prompt, style)

        # 呼叫 DALL·E 3 API
        resp = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
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
