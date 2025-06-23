# -*- coding: utf-8 -*-
# info_handler.py
# 本模組處理通用人物資訊查詢：身分介紹、生日查詢、時間查詢及其他屬性問題

import re
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI, OpenAIError
from search_web import search_all_sources

client = OpenAI()

# 設定使用台北時區
TZ = ZoneInfo("Asia/Taipei")

# —— 即時時間查詢 ——  
def is_time_query(text: str) -> bool:
    return bool(re.search(r"現在\s*幾點", text))

def handle_time_query() -> str:
    now = datetime.now(TZ)
    return f"現在台北時間是 {now.strftime('%H:%M')}。"

# —— 是誰查詢 ——  
def is_who_query(text: str) -> bool:
    return bool(re.search(r"(?:請問\s*)?(.+?)\s*是誰", text))

def handle_who_query(text: str) -> str:
    name = extract_person_name(text)
    return get_who_info(name)

# —— 生日查詢 ——  
def is_birthday_query(text: str) -> bool:
    return bool(re.search(r"(?:請問\s*)?(.+?)\s*(?:的)?(?:生日|出生日期)", text))

def handle_birthday_query(text: str) -> str:
    name = extract_person_name(text)
    bd = get_birthdate(name)
    if re.match(r"\d{4}-\d{2}-\d{2}", bd):
        now = datetime.now(TZ).date()
        y, m, d = map(int, bd.split("-"))
        age = now.year - y - ((now.month, now.day) < (m, d))
        return f"『{name}』出生於 {bd}，截至 {now}，年齡為 {age} 歲。"
    return bd

# —— 泛用屬性查詢 ——  
def is_general_info_query(text: str) -> bool:
    return bool(re.search(r"請問\s*(.+?)\s*(?:他|她|TA)\s*(.+)\?*", text))

def handle_general_info_query(text: str) -> str:
    name = extract_person_name(text)
    attr = extract_general_attribute(text)
    prompt = f"請提供『{name}』的{attr}，需依據公開資訊並簡要回答。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        ans = resp.choices[0].message.content.strip()
        if not ans or any(k in ans for k in ["不知道", "抱歉"]):
            raise ValueError("GPT 未返回有效資訊")
        return ans
    except (OpenAIError, ValueError):
        return search_all_sources(f"{name} {attr}")

# —— 萃取人名與屬性 ——  
def extract_person_name(text: str) -> str:
    match = re.search(r"(?:請問\s*)?(.+?)\s*(?:是誰|的?生日|出生日期|他|她|TA)", text)
    return match.group(1).strip() if match else text.strip()

def extract_general_attribute(text: str) -> str:
    match = re.search(r"請問\s*(?:.+?)\s*(?:他|她|TA)\s*(.+)\?*", text)
    return match.group(1).strip() if match else text.strip()

# —— GPT + 網路搜尋後備 ——  
def get_who_info(name: str) -> str:
    prompt = f"請提供簡潔明確的『{name}』介紹，包括身份背景，字數不要超過兩句。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        info = resp.choices[0].message.content.strip()
        if not info or any(k in info for k in ["不知道", "抱歉"]):
            raise ValueError("GPT 未返回有效資訊")
        return info
    except (OpenAIError, ValueError):
        return search_all_sources(name)


def get_birthdate(name: str) -> str:
    prompt = f"請僅回傳『{name}』的出生日期，格式 YYYY-MM-DD；如無公開資訊請回覆 UNKNOWN。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        bd = resp.choices[0].message.content.strip()
        if not re.match(r"\d{4}-\d{2}-\d{2}", bd):
            raise ValueError("格式不符")
        return bd
    except (OpenAIError, ValueError):
        return search_all_sources(f"{name} 出生日期")
