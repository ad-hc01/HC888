# -*- coding: utf-8 -*-
# 本檔案負責查詢 PTX 運輸資料（高鐵），並回傳純文字班次資訊

import os
import datetime
import httpx
from linebot.v3.messaging import TextMessage as V3TextMessage

# 從環境變數讀取 PTX App ID / Key
TDX_APP_ID = os.getenv("TDX_APP_ID")
TDX_APP_KEY = os.getenv("TDX_APP_KEY")

def get_tdx_headers() -> dict[str, str]:
    """
    回傳 PTX API 所需標頭（含 AppID/Key）
    """
    return {
        "accept": "application/json",
        "x-ptx-app-id": TDX_APP_ID or "",
        "x-ptx-app-key": TDX_APP_KEY or ""
    }

def get_thsr_schedule(
    origin: str = "Taipei",
    destination: str = "Taichung",
    date: str | None = None
) -> V3TextMessage:
    """
    查詢高鐵班次，回傳純文字格式的 LINE 訊息。
    :param origin: 起始站（英文）
    :param destination: 終點站（英文）
    :param date: 日期，格式 YYYY-MM-DD，預設為今日
    :return: V3TextMessage
    """
    if not TDX_APP_ID or not TDX_APP_KEY:
        return V3TextMessage(text="❌ 未設定 PTX API 金鑰，無法查詢運輸資訊。")

    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        url = (
            f"https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/DailyTimetable/OD/"
            f"{origin}/to/{destination}/{date}?$format=JSON"
        )
        resp = httpx.get(url, headers=get_tdx_headers(), timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, list) or not data:
            return V3TextMessage(text=f"❌ {origin}→{destination} 在 {date} 無查到任何班次。")

        # 組裝班次文字
        lines = [f"🚄 高鐵班次 {origin}→{destination} ({date}):"]
        for entry in data[:5]:
            info = entry.get("DailyTrainInfo", {})
            ori = entry.get("OriginStopTime", {})
            dst = entry.get("DestinationStopTime", {})
            train_no = info.get("TrainNo", "N/A")
            dep_time = ori.get("DepartureTime", "")
            arr_time = dst.get("ArrivalTime", "")
            lines.append(f"- {train_no}: {dep_time} → {arr_time}")
        lines.append("更多班次請至高鐵官網：https://www.thsrc.com.tw")

        return V3TextMessage(text="\n".join(lines))

    except httpx.RequestError as e:
        print(f"[get_thsr_schedule] Request error: {e}")
    except Exception as e:
        print(f"[get_thsr_schedule] Unexpected error: {e}")

    return V3TextMessage(text="⚠️ 查詢高鐵資訊失敗，請稍後再試。")
