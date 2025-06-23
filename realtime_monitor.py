# -*- coding: utf-8 -*-
# 本模組為網站驗證題目監聽器，從 LINE 指令動態觸發，偵測指定題目區塊並推播 LINE 群組

import threading
import time
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging.models import TextMessage as V3TextMessage, PushMessageRequest

CHECK_INTERVAL = 60  # 檢查間隔秒數

monitor_thread = None          # 執行緒物件
monitor_stop_event = None      # 停止旗標

def start_monitor(url: str, group_id: str, line_api: MessagingApi) -> str:
    global monitor_thread, monitor_stop_event

    if monitor_thread and monitor_thread.is_alive():
        return "⚠️ 已有監聽任務執行中，請先停止。"

    monitor_stop_event = threading.Event()

    def loop():
        while not monitor_stop_event.is_set():
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                title_el = soup.select_one(".promo-title")
                desc_el = soup.select_one(".promo-desc")
                input_el = soup.select_one('input[name="checkCode"]')

                if title_el and desc_el and input_el:
                    msg = (
                        "🎯 發現驗證題目區塊！\n"
                        f"📌 區塊標題：{title_el.get_text(strip=True)}\n"
                        f"📝 題目內容：{desc_el.get_text(strip=True)}\n"
                        f"🧩 已出現填空欄位 name=checkCode"
                    )
                    line_api.push_message(PushMessageRequest(
                        to=group_id,
                        messages=[V3TextMessage(text=msg)]
                    ))
                else:
                    print("[偵測中] 尚未出現完整題目結構")
            except Exception as e:
                print(f"[錯誤] 擷取失敗：{e}")
            time.sleep(CHECK_INTERVAL)

    monitor_thread = threading.Thread(target=loop, daemon=True)
    monitor_thread.start()
    return f"✅ 已啟動監聽：{url}"

def stop_monitor() -> str:
    global monitor_thread, monitor_stop_event
    if monitor_thread and monitor_thread.is_alive():
        monitor_stop_event.set()
        return "🛑 已停止監聽"
    return "ℹ️ 目前沒有監聽任務在執行中"

def get_monitor_status() -> str:
    if monitor_thread and monitor_thread.is_alive():
        return "📡 監聽中..."
    return "🔕 未在監聽狀態"
