# -*- coding: utf-8 -*-
# 本模組為網站標題變更監聽器，偵測特定網址的 title 或內文是否有變動，並推播通知至指定群組

import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage as V3TextMessage, PushMessageRequest

MONITORED_URL = "https://www.example.com"
GROUP_ID = "C6c465dd5a162fd79182d7b92eccc2d57"
CHECK_INTERVAL = 60

config = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_api = MessagingApi(api_client=ApiClient(config))

last_title = None
_monitor_thread = None
_monitor_stop_event = threading.Event()

def fetch_title(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("title")
        return title_tag.text.strip() if title_tag else "(無標題)"
    except Exception as e:
        return f"(無法取得標題: {e})"

def _monitor_title():
    global last_title
    while not _monitor_stop_event.is_set():
        current_title = fetch_title(MONITORED_URL)
        if last_title is not None and current_title != last_title:
            msg = f"🔔 網站標題已變更！\n原本：{last_title}\n現在：{current_title}"
            try:
                line_api.push_message(
                    PushMessageRequest(
                        to=GROUP_ID,
                        messages=[V3TextMessage(text=msg)]
                    )
                )
            except Exception as e:
                print(f"[錯誤] 推播失敗：{e}")
        last_title = current_title
        _monitor_stop_event.wait(CHECK_INTERVAL)

def start_monitor(url=None, group_id=None, api=None):
    global MONITORED_URL, GROUP_ID, line_api, _monitor_thread, _monitor_stop_event

    if url:
        MONITORED_URL = url
    if group_id:
        GROUP_ID = group_id
    if api:
        line_api = api

    if _monitor_thread and _monitor_thread.is_alive():
        return "監聽已經在執行中"

    _monitor_stop_event.clear()
    _monitor_thread = threading.Thread(target=_monitor_title, daemon=True)
    _monitor_thread.start()
    return f"開始監聽網址：{MONITORED_URL}"

def stop_monitor():
    global _monitor_stop_event, _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_stop_event.set()
        _monitor_thread.join()
        return "監聽已停止"
    else:
        return "目前沒有監聽中的任務"

def get_monitor_status():
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        return f"監聽中網址：{MONITORED_URL}"
    else:
        return "目前沒有監聽任務"
