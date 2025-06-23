# -*- coding: utf-8 -*-
# age_handler.py
# 本模組用於通用年齡查詢：偵測使用者年齡問題，呼叫 GPT 取得生日，再計算並回傳年齡
import re
from datetime import date
from openai import OpenAI, OpenAIError

client = OpenAI()

def is_age_query(text: str) -> bool:
    return bool(re.search(r"幾歲|多少歲", text))

def extract_person_name(text: str) -> str:
    match = re.search(r"(?:的\s*)?([\u4e00-\u9fa5A-Za-z0-9\s]+?)\s*(?:幾歲|多少歲)", text)
    return match.group(1).strip() if match else text.strip()

def get_birthdate(name: str) -> str:
    prompt = f"請提供名為『{name}』的公開人物出生日期，格式僅限 YYYY-MM-DD，若無公開資料請回覆 UNKNOWN。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是專業資料查詢助手，僅回傳生日或 UNKNOWN。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError:
        return "UNKNOWN"

def calculate_age(birthdate: str, today: date = date.today()) -> int | None:
    try:
        y, m, d = map(int, birthdate.split('-'))
        bd = date(y, m, d)
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        return age
    except Exception:
        return None

def handle_age_query(text: str) -> str:
    name = extract_person_name(text)
    bd = get_birthdate(name)
    if bd == "UNKNOWN":
        return f"抱歉，找不到『{name}』的出生日期資訊，無法計算年齡。"
    age = calculate_age(bd)
    if age is None:
        return f"取得『{name}』的生日 ({bd}) 後，計算年齡時發生錯誤。"
    today = date(2025, 6, 23)
    return f"{name} 出生於 {bd}，截至 {today}，年齡為 {age} 歲。"
