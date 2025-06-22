# -*- coding: utf-8 -*-
# 本檔案為 GPT 對話處理模組，處理上下文、風格注入、使用者知識學習與延伸建議

import os
from openai import OpenAI

# 初始化 OpenAI 客戶端，從環境變數自動讀取 API 金鑰
client = OpenAI()


def generate_gpt_reply(user_id: str,
                       user_msg: str,
                       history: list[dict],
                       user_name: str,
                       ai_name: str,
                       style: str,
                       facts: list[str] | None = None) -> str:
    """
    組裝 GPT 對話請求，加入風格、使用者知識與延伸建議提示。
    :param facts: 使用者個人知識記憶（可選）
    """
    # 風格指令模板
    style_prompts = {
        "正式風": "請以專業且客觀的方式回答問題。",
        "可愛風": "請用可愛、貼近人心的語氣回答，偶爾加點 emoji。",
        "幽默風": "請用幽默、輕鬆、有趣的方式回答問題，適度加點笑點。",
        "科學風": "請以嚴謹邏輯、條列清晰方式，像科學家一樣回答。",
        "生活風": "請以親切、口語、像朋友一樣的語氣來回答。"
    }
    style_instruction = style_prompts.get(style, style_prompts["正式風"])

    # 使用者知識注入
    facts_prompt = ""
    if facts:
        facts_prompt = "\n\n以下是使用者的個人資訊，請一併參考：\n" + "\n".join(f"- {f}" for f in facts)

    # 延伸建議提示
    suggest_prompt = (
        "請在回答後，自動補充 2~3 條與此主題相關的延伸建議或應用方向，幫助使用者舉一反三。"
    )

    system_prompt = f"""
你是一位智慧 AI 輔導老師，名稱是「{ai_name}」，你的任務是根據使用者的語氣與習慣回應。
{style_instruction}
如果問題涉及事實或使用者資訊，可參考他過往提供的資料。{facts_prompt}
{suggest_prompt}
""".strip()

    # 組裝訊息
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        # 使用新版 OpenAI 客戶端
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # 回傳友善錯誤訊息
        return f"⚠️ 發生錯誤，無法取得回答。{e}"
