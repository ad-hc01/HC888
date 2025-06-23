# -*- coding: utf-8 -*-
# 本模組為網站標題即時監聽器，支援從主程式即時啟動/停止，並推播變更通知。
# 加強：URL驗證、防重啟、防洗版、連錯5次自停、授權群組限制（從環境變數）

import os
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from linebot.v3.messaging import MessagingApi, TextMessage as V3TextMessage

ALLOWED_GROUP_ID = os.getenv("LINE_NOTIFY_GROUP_ID")  # ✅ 從環境變數取得授權群組ID
MIN_INTERVAL = 0.5
MAX_INTERVAL = 10.0
MAX_FAILURES = 5

monitor_data = {
    "url": None,
    "interval": None,
    "title": None,
    "timer": None,
    "group_id": None,
    "line_api": None,
    "fail_count": 0,
    "last_error": None
}

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc != ""

def _monitor_title():
    url = monitor_data["url"]
    group_id = monitor_data["group_id"]
    line_api = monitor_data["line_api"]

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        new_title = soup.title.string.strip() if soup.title else "(無標題)"

        if monitor_data["title"] != new_title:
            monitor_data["title"] = new_title
            monitor_data["fail_count"] = 0  # 成功即清零
            msg = f"📡 網站標題更新：\n{url}\n➡️ {new_title}"
            line_api.push_message(group_id, [V3TextMessage(text=msg)])

    except Exception as e:
        monitor_data["fail_count"] += 1
        error_str = str(e)
        if error_str != monitor_data["last_error"]:
            monitor_data["last_error"] = error_str
            msg = f"⚠️ 無法連線：{url}\n原因：{e}"
            line_api.push_message(group_id, [V3TextMessage(text=msg)])

        # 自動停止：連錯 5 次
        if monitor_data["fail_count"] >= MAX_FAILURES:
            stop_monitor()
            line_api.push_message(group_id, [V3TextMessage(text="⛔ 連續錯誤已達 5 次，自動停止監聽")])
            return

    if monitor_data["url"]:
        monitor_data["timer"] = threading.Timer(monitor_data["interval"], _monitor_title)
        monitor_data["timer"].start()

def start_monitor(raw: str, group_id: str, line_api: MessagingApi) -> str:
    if group_id != ALLOWED_GROUP_ID:
        return "🚫 你沒有啟動監聽的權限"

    import re
    match = re.match(r"(.+)\s+(\d+(\.\d+)?)(秒)?", raw.strip())
    if not match:
        return "❌ 格式錯誤，請使用：啟動監聽: https://網址 5秒"

    url = match.group(1)
    try:
        interval = float(match.group(2))
    except:
        return "❌ 時間格式錯誤，請用 0.5~10 秒"

    if not is_valid_url(url):
        return "❌ 網址格式不正確，請以 http(s):// 開頭"

    if not (MIN_INTERVAL <= interval <= MAX_INTERVAL):
        return f"⚠️ 允許的間隔為 {MIN_INTERVAL}～{MAX_INTERVAL} 秒"

    if monitor_data["timer"] and monitor_data["timer"].is_alive():
        return "⚠️ 已有監聽任務執行中，請先停止再啟動"

    stop_monitor()
    monitor_data.update({
        "url": url,
        "interval": interval,
        "title": None,
        "group_id": group_id,
        "line_api": line_api,
        "fail_count": 0,
        "last_error": None,
    })
    monitor_data["timer"] = threading.Timer(0.1, _monitor_title)
    monitor_data["timer"].start()
    return f"✅ 已啟動監聽：{url}（每 {interval} 秒）"

def stop_monitor() -> str:
    if monitor_data["timer"]:
        monitor_data["timer"].cancel()
    monitor_data.update({"url": None, "interval": None, "title": None, "timer": None})
    return "🛑 已停止監聽"

def get_monitor_status() -> str:
    if monitor_data["url"]:
        return f"🟢 正在監聽：{monitor_data['url']}（每 {monitor_data['interval']} 秒）"
    else:
        return "⚪ 目前沒有任何監聽任務"
