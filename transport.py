# -*- coding: utf-8 -*-
# 本檔案提供高鐵、台鐵、與航班時刻查詢功能，改為純文字格式回傳使用者

def get_thsr_schedule(query: str) -> str:
    # 模擬回傳高鐵資訊，可接 API 後擴充
    return f"🚄 高鐵時刻查詢結果：\n你查詢的是：{query}\n（此處可接高鐵 API 顯示車次、出發與抵達時間）"

def get_tra_schedule(query: str) -> str:
    return f"🚆 台鐵時刻查詢結果：\n你查詢的是：{query}\n（此處可接台鐵 API 顯示對應資訊）"

def get_flight_schedule(query: str) -> str:
    return f"🛫 航班查詢結果：\n你查詢的是：{query}\n（此處可接航班 API 顯示起飛、抵達與狀態）"
