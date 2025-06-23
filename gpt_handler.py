# -*- coding: utf-8 -*-
# 本檔案為 GPT 對話處理模組，處理上下文、風格注入、使用者知識學習

import os
from openai import OpenAI

# 初始化 OpenAI 客戶端
client = OpenAI()

def generate_gpt_reply(user_id: str,
                       user_msg: str,
                       history: list[dict],
                       user_name: str,
                       ai_name: str,
                       style: str,
                       facts: list[str] | None = None) -> str:
    """
    組裝 GPT 對話請求，加入語氣風格與使用者知識
    """
    style_prompts = {
        "正式風": "你是一位有禮貌且專業的助理，回答簡潔清楚，不插科打諢。",
        "可愛風": "你是一個超級可愛的角色，語氣像卡通人物一樣俏皮，讓人聽了會笑。",
        "幽默風": "你是一個風趣幽默的朋友，回話要活潑有梗，像是在聊天。",
        "生活風": "你說話自然不造作，像鄰居或朋友一樣，舉例貼近日常。",
        "科學風": "你是一位具邏輯與數據導向的科學家，重視推理與事實。"
    }
    style_instruction = style_prompts.get(style, style_prompts["正式風"])

    # 使用者知識注入
    facts_prompt = ""
    if facts:
        facts_prompt = "\n以下是使用者的個人資訊，可納入回應背景：\n" + "\n".join(f"- {f}" for f in facts)

    system_prompt = f"""
你是名叫 {ai_name} 的 GPT 助理，說話風格要符合使用者偏好，親切、自然、像人一樣口語化。
{style_instruction}
請用流暢敘述方式作答，避免條列式（1. 2. 3.）或公式教學語氣。
如果問題涉及事實，可結合使用者提供的資訊。{facts_prompt}
""".strip()

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 發生錯誤，無法取得回答。{e}"
