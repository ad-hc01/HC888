# -*- coding: utf-8 -*-
# 本檔案負責處理 YouTube 影片與音訊 direct URL 擷取（不下載、不儲存）

from yt_dlp import YoutubeDL
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage as V3TextMessage

def handle_youtube_download(event, api: MessagingApi, media_type: str = "video"):
    """
    解析使用者傳來的「下載影片」或「下載音訊」指令，
    從 YouTube 取得 direct URL 回傳給用戶（僅提供鏈結）。
    :param event: LINE Webhook 傳來的 MessageEvent
    :param api: 已初始化的 MessagingApi 實例
    :param media_type: "video" 或 "audio"
    """
    text = event.message.text.strip()
    # 去除指令關鍵字，取得純粹 URL
    url = (
        text
        .replace("下載影片", "")
        .replace("下載音訊", "")
        .replace("下載音樂", "")
        .strip()
    )

    # 驗證 URL
    if not url.lower().startswith("http"):
        req = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text="❌ 請提供正確的 YouTube 連結。")]
        )
        api.reply_message(req)
        return

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio/best" if media_type == "audio" else "bestvideo+bestaudio/best"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "影片")
            # 直接使用 yt_dlp 幫我們挑好的格式
            formats = info.get("formats") or [info]
            download_url = None
            # 如果 yt_dlp 已根據 format 選好了 URL，就直接取第一筆
            if formats:
                download_url = formats[0].get("url")

        if not download_url:
            raise ValueError("找不到可用的下載連結")

        reply_text = (
            f"✅ 以下是「{title}」的 direct 下載連結：\n"
            f"請在電腦瀏覽器中打開並另存：\n{download_url}"
        )
        req = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text=reply_text)]
        )
        api.reply_message(req)

    except Exception as e:
        # 若要更詳盡的除錯，可改用 logging 套件
        print("[handle_youtube_download] Error:", e)
        req = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text="❌ 抱歉，無法擷取下載連結，請稍後再試。")]
        )
        api.reply_message(req)
