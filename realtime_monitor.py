# -*- coding: utf-8 -*-
# 本模組為網站標題變更監聽器，偵測特定網址的 title 或內文是否有變動，並推播通知至指定群組

import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage as V3TextMessage, PushMessageRequest

# 監聽目標網址
MONITORED_URL = "https://www.example.com"

# LINE 群組 ID（專用通知）
GROUP_ID = "C6c465dd5a162fd79182d7b92eccc2d57"

# 設定間隔時間（秒）
CHECK_INTERVAL = 60

# 初始化 LINE API
config = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_api = MessagingApi(api_client=ApiClient(config))

# 記錄前一次的標題
last_title = None

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
    while True:
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
        time.sleep(CHECK_INTERVAL)

def start_monitor():
    thread = threading.Timer(5.0, _monitor_title)
    thread.daemon = True
    thread.start()
