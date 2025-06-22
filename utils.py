# -*- coding: utf-8 -*-
# 本檔案為指令解析模組，處理命名、風格切換、知識記憶等行為

import re

def is_stylegen_request(text: str) -> bool:
    return "幫我生成" in text and "風格" in text

def is_translate_request(text):
    return text.startswith("翻譯 ")

def extract_user_name(text):
    """提取使用者自訂名稱"""
    match = re.match(r"(你)?要叫我[:：]?(.+)", text)
    return match.group(2).strip() if match else None

def extract_user_style(text):
    """提取使用者切換的風格"""
    match = re.search(r"(幫我|切換為)?(.+風)", text)
    return match.group(2).strip() if match else None

def extract_user_fact(text):
    """提取要記住的知識，例如「記住我喜歡貓」"""
    if text.startswith("記住") or text.startswith("幫我記住"):
        return text.replace("幫我記住", "").replace("記住", "").strip()
    return None

def is_clear_facts(text):
    return "清除知識" in text or "忘記我說的" in text

def is_image_request(text):
    return "生成圖片" in text or "畫一張" in text

def is_video_request(text):
    return "youtube" in text.lower()

def is_transport_request(text):
    keywords = ["高鐵", "台鐵", "航班", "飛機"]
    return any(k in text for k in keywords)

def is_map_request(text):
    return "地圖" in text

def is_draw_request(text):
    return "抽" in text and ("運勢" in text or "塔羅" in text or "自訂" in text or "、" in text)

def is_weather_request(text):
    return "天氣" in text

def is_help_request(text: str) -> bool:
    """判斷是否為幫助請求（功能清單/教學）"""
    keywords = ["功能", "幫助", "教學", "指令", "help"]
    return any(kw in text.lower() for kw in keywords)
