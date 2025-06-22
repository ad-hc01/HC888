# -*- coding: utf-8 -*-
# 本模組用於處理翻譯功能，使用 GPT-4o 將指定文字翻譯為目標語言

import openai

def translate_text(original_text: str, target_language: str) -> str:
    prompt = f"請將以下句子翻譯成 {target_language}：{original_text}"

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位語言翻譯專家，請準確地進行翻譯。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "翻譯時發生錯誤，請稍後再試。"
