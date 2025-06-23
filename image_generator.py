# -*- coding: utf-8 -*-
# 本檔案負責處理使用者圖片生成請求，透過 DALL·E 3 並回傳給 LINE 用戶
# 已整合：敏感詞過濾 + 風格細化提示生成 + 完整錯誤回傳

from openai import OpenAI, OpenAIError
from linebot.v3.messaging import TextMessage as V3TextMessage, ImageMessage as V3ImageMessage
from prompt_enhancer import enhance_prompt_with_style

client = OpenAI()

SENSITIVE_KEYWORDS = ["裸體", "色情", "暴力", "血腥", "自殺", "仇恨"]


def is_sensitive(prompt: str) -> bool:
    """判斷是否含有敏感關鍵字，若有則拒絕生成。"""
    return any(kw in prompt for kw in SENSITIVE_KEYWORDS)


def generate_image_message(text: str):
    """
    使用者輸入如：「幫我生成 洛可可風格的貓咪插畫」
    自動分離風格關鍵詞（若有），再注入 prompt_enhancer 強化提示，最後送至 DALL·E 3 生成圖片。
    """
    # Debug log
    print(f"[DEBUG] generate_image_message called with: {text!r}")

    # 敏感詞過濾
    if is_sensitive(text):
        return V3TextMessage(text="❌ 這類圖片無法提供，請嘗試其他主題～")

    # 分離風格與主題
    style = ""
    prompt = text.strip()
    if "風格" in text and "生成" in text:
        # 範例：幫我生成 洛可可風格的貓咪插畫
        parts = text.replace("幫我生成", "").replace("風格", "").strip().split("的", 1)
        style = parts[0].strip()
        prompt = parts[1].strip() if len(parts) > 1 else prompt

    # 強化提示
    try:
        enhanced_prompt = enhance_prompt_with_style(prompt, style)
    except Exception as e:
        # 若 prompt_enhancer 出問題，回傳並顯示錯誤
        err_text = f"❌ 強化提示失敗：{type(e).__name__} - {e}"
        print(f"[ERROR] enhance_prompt_with_style: {e}")
        return V3TextMessage(text=err_text)

    # 呼叫 DALL·E 3 API
    try:
        resp = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = resp.data[0].url
        print(f"[DEBUG] DALL·E 生成成功 URL: {image_url}")
        return V3ImageMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )

    except OpenAIError as e:
        err = f"❌ DALL·E 3 生成失敗：{e}"
        print(f"[ERROR] generate_image_message OpenAIError: {e}")
        return V3TextMessage(text=err)
    except Exception as e:
        err = f"❌ 圖片生成流程異常：{type(e).__name__} - {e}"
        print(f"[ERROR] generate_image_message Unexpected: {e}")
        return V3TextMessage(text=err)
