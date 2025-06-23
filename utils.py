# -*- coding: utf-8 -*-
# 本檔案為指令解析模組，處理命名、風格切換、知識記憶、媒體與搜尋等行為

import re
from typing import Optional

def is_stylegen_request(text: str) -> bool:
    return "幫我生成" in text and "風格" in text

def is_prompt_enhance_request(text: str) -> bool:
    """判斷是否為圖片主題生成，需啟動風格細化提示生成功能"""
    return any(x in text for x in ["畫", "生成圖片", "幫我畫", "想像圖", "幫我生成"])

def is_translate_request(text: str) -> bool:
    return text.strip().startswith("翻譯 ")

def is_meihua_request(text):
    return "梅花易數" in text or "起卦" in text or "梅花卜卦" in text

def extract_user_name(text: str) -> Optional[str]:
    match = re.match(r"(?:你)?要叫我[:：]?\s*(.+)", text)
    return match.group(1).strip() if match else None

def extract_ai_name(text: str) -> Optional[str]:
    match = re.match(r"(?:你)?叫做[:：]?\s*(.+)", text)
    return match.group(1).strip() if match else None

def extract_user_style(text: str) -> Optional[str]:
    match = re.match(r"(?:切換風格|風格)[:：]?\s*(.+)", text)
    return match.group(1).strip() if match else None

def extract_user_fact(text: str) -> Optional[str]:
    match = re.match(r"(?:記住|我想讓你知道)[:：]?\s*(.+)", text)
    return match.group(1).strip() if match else None

def is_clear_facts(text: str) -> bool:
    return text.strip() in ["清空知識", "忘掉我剛剛說的", "忘記知識", "重置記憶"]

def is_image_request(text: str) -> bool:
    return any(kw in text for kw in ["畫", "生成圖片", "幫我畫", "想像圖"])

def is_imagegen_request(text: str) -> bool:
    # 直接呼叫 is_image_request 判斷圖片生成請求
    return is_image_request(text)

def is_video_request(text: str) -> bool:
    return any(kw in text for kw in ["播放", "MV", "YouTube", "推薦影片", "影片"])

def is_transport_request(text: str) -> bool:
    return any(kw in text for kw in ["高鐵", "台鐵", "航班", "班次", "車次"])

def is_map_request(text: str) -> bool:
    keywords = ["地圖", "在哪", "怎麼走", "地址", "地點", "map", "location"]
    return any(kw in text.lower() for kw in keywords)

def is_draw_request(text: str) -> bool:
    return any(kw in text for kw in ["抽卡", "塔羅", "運勢", "自訂抽"])

def is_weather_request(text: str) -> bool:
    return "天氣" in text

def is_help_request(text: str) -> bool:
    return text.strip().lower() in ["help", "幫助", "？", "?"]
