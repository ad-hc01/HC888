# -*- coding: utf-8 -*-
# info_handler.py
# 本模組處理通用人物資訊查詢：身分介紹、年齡查詢、生日查詢、出道查詢、專輯查詢、時間查詢及其他屬性問題

import re
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI, OpenAIError
from search_web import search_all_sources

client = OpenAI()
TZ = ZoneInfo("Asia/Taipei")

# —— 查詢類型判斷 ——
def is_time_query(text): return "現在幾點" in text

def is_age_query(text): return bool(re.search(r"幾歲|年齡", text))

def is_birthday_query(text): return bool(re.search(r"生日|出生日期", text))

def is_debut_query(text): return "出道" in text and not is_birthday_query(text)

def is_album_query(text): return bool(re.search(r"專輯|唱片", text))

def is_who_query(text): return bool(re.search(r"是誰", text))

def is_general_info_query(text):
    return bool(re.search(r"請問\s*(.+?)\s*(?:他|她|TA)\s*(.+)", text))

# —— 即時時間查詢 ——
def handle_time_query():
    now = datetime.now(TZ)
    return f"🕒 現在台北時間是 {now.strftime('%H:%M')}。"

# —— 年齡查詢 ——
def handle_age_query(text):
    name = extract_person_name(text)
    prompt = f"請問『{name}』目前幾歲？請僅回傳年齡數字（例如：20）。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        age = resp.choices[0].message.content.strip()
        if not re.match(r"^\d{1,3}$", age):
            raise ValueError("GPT 回傳格式錯誤")
        return f"『{name}』目前 {age} 歲。"
    except (OpenAIError, ValueError):
        query = f"{name} 年齡"
        return f"📡 查詢失敗，改為網路搜尋：\n{search_all_sources(query)}"

# —— 生日查詢 ——
def handle_birthday_query(text):
    name = extract_person_name(text)
    bd = get_birthdate(name)
    if re.match(r"\d{4}-\d{2}-\d{2}", bd):
        today = datetime.now(TZ).date()
        y, m, d = map(int, bd.split("-"))
        age = today.year - y - ((today.month, today.day) < (m, d))
        return f"『{name}』出生於 {y} 年 {m} 月 {d} 日，截至今天 {today}，她 {age} 歲。"
    return f"📡 查不到『{name}』的出生日期，以下是網路結果：\n{bd}"

# —— 出道日期查詢 ——
def handle_debut_query(text):
    name = extract_person_name(text)
    result = search_all_sources(f"{name} 出道日期")
    m = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", result)
    if m:
        y, mth, d = m.groups()
        return f"『{name}』於 {y} 年 {mth} 月 {d} 日 出道。"
    return f"📡 查不到明確出道日期，以下網路結果：\n{result}"

# —— 專輯列表查詢 ——
def handle_album_query(text):
    name = extract_person_name(text)
    result = search_all_sources(f"{name} 發行 專輯 列表")
    # 嘗試從結果中抓出專輯名稱（取最多10項）
    albums = re.findall(r"·\s*([^\n·]+)", result)
    if albums:
        return f"『{name}』曾發行的專輯有：{ '、'.join(albums[:10]) }。"
    return f"📡 查不到完整列表，以下是網路結果：\n{result}"

# —— 是誰查詢 ——
def handle_who_query(text):
    name = extract_person_name(text)
    return get_who_info(name)

# —— 泛用屬性查詢 ——
def handle_general_info_query(text):
    name = extract_person_name(text)
    attr = extract_general_attribute(text)
    prompt = f"請簡要回答『{name}』的{attr}，依據公開資訊，一句話即可。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        ans = resp.choices[0].message.content.strip()
        if not ans or any(k in ans for k in ["不知道", "無法", "查無"]):
            raise ValueError("GPT 無效回應")
        return f"『{name}』的{attr}是：{ans}"
    except (OpenAIError, ValueError):
        return f"📡 查詢失敗，改為網路搜尋：\n{search_all_sources(f'{name} {attr}') }"

# —— GPT + fallback ——
def get_who_info(name):
    prompt = f"請用一句話簡要介紹『{name}』的身份或背景。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        info = resp.choices[0].message.content.strip()
        if not info or "不知道" in info:
            raise ValueError
        return info
    except (OpenAIError, ValueError):
        return f"📡 以下是網路搜尋結果：\n{search_all_sources(name)}"

# —— 擷取出生日期 ——
def get_birthdate(name):
    prompt = f"請回傳『{name}』的出生日期，格式 YYYY-MM-DD；若查無資料請回 UNKNOWN。"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        bd = resp.choices[0].message.content.strip()
        if not re.match(r"\d{4}-\d{2}-\d{2}", bd):
            raise ValueError
        return bd
    except (OpenAIError, ValueError):
        return search_all_sources(f"{name} 出生日期")

# —— 抽取人名與屬性 ——
def extract_person_name(text):
    m = re.search(r"(.+?)團體.*的(.+?)(?:幾歲|年齡|出生|出道|專輯)?", text)
    if m:
        grp, member = m.groups()
        return f"{grp} 的 {member}"
    m2 = re.search(r"(?:請問\s*)?(.+?)\s*(?:是誰|的?生日|出生日期|幾歲|年齡|出道|專輯)?", text)
    return m2.group(1).strip() if m2 else text.strip()

def extract_general_attribute(text):
    m = re.search(r"請問\s*(?:.+?)\s*(?:他|她|TA)\s*(.+)", text)
    return m.group(1).strip() if m else "資料"
