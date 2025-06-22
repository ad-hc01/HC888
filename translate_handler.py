# -*- coding: utf-8 -*-
# 本模組用於處理翻譯功能，使用 GPT-4o 將指定文字翻譯為目標語言

from openai import OpenAI, OpenAIError

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

def translate_text(original_text: str, target_language: str) -> str:
    """
    將 original_text 精確地翻譯成 target_language。
    :param original_text: 要翻譯的原文
    :param target_language: 目標語言（如「英文」、「日文」）
    :return: 翻譯結果字串
    """
    prompt = f"請將以下句子精確翻譯成 {target_language}：\n{original_text}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位專業的翻譯專家，請精確地將內容翻譯成目標語言，不要添加多餘說明。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"[translate_text] OpenAI API error: {e}")
    except Exception as e:
        print(f"[translate_text] Unexpected error: {e}")
    return "⚠️ 翻譯時發生錯誤，請稍後再試。"
