# -*- coding: utf-8 -*-
# 本檔案為 GPT 對話處理模組，處理上下文、風格注入、使用者知識學習與延伸建議，使用 OpenAI SDK v1.55.3 寫法

import os
import httpx
from openai import OpenAI

# Render 等雲端環境已設定 API key，無需 load_dotenv
# load_dotenv() 移除以避免混淆

# 從環境變數取得金鑰（Render 等平台會自動注入）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 使用自訂 httpx client（新版 openai 支援）
httpx_client = httpx.Client()
client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx_client)

def generate_gpt_reply(user_id, user_msg, history, user_name, ai_name, style, facts=None):
    """
    組裝 GPT 對話請求，加入風格、使用者知識與延伸建議提示。
    :param facts: list[str] 使用者個人知識記憶（可選）
    """
    style_prompts = {
        "正式風": "請以專業且客觀的方式回答問題。",
        "可愛風": "請用可愛、貼近人心的語氣回答，偶爾加點 emoji。",
        "幽默風": "請用幽默、輕鬆、有趣的方式回答問題，適度加點笑點。",
        "科學風": "請以嚴謹邏輯、條列清晰方式，像科學家一樣回答。",
        "生活風": "請以親切、口語、像朋友一樣的語氣來回答。"
    }
    style_instruction = style_prompts.get(style, style_prompts["正式風"])

    # 使用者知識注入（如有）
    facts_prompt = ""
    if facts:
        facts_prompt = "\n\n以下是使用者的個人資訊，請一併參考：\n" + "\n".join(f"- {fact}" for fact in facts)

    # 延伸建議提示
    suggest_prompt = "請在回答後，自動補充 2~3 條與此主題相關的延伸建議或應用方向，幫助使用者舉一反三。"

    system_prompt = f"""
你是一位智慧 AI 輔導老師，名稱是「{ai_name}」，你的任務是根據使用者的語氣與習慣回應。
{style_instruction}
如果問題涉及事實或使用者資訊，可參考他過往提供的資料。{facts_prompt}
{suggest_prompt}
"""

    messages = [{"role": "system", "content": system_prompt.strip()}]
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
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
        return f"⚠️ 發生錯誤，無法取得回答。\n\n{e}"
