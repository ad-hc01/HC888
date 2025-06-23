# -*- coding: utf-8 -*-
# 本檔案負責處理 YouTube 影片與音訊 direct URL 擷取（不下載、不儲存）

from yt_dlp import YoutubeDL
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage as V3TextMessage
import re

def clean_title(title):
    """移除影片標題中的奇怪符號或 emoji，避免傳送失敗"""
    return re.sub(r"[^\w\s\u4e00-\u9fff]", "", title)

def handle_youtube_download(event, api: MessagingApi, media_type: str = "video"):
    """
    解析使用者傳來的「下載影片」或「下載音訊」指令，
    從 YouTube 取得 direct URL 回傳給用戶（僅提供鏈結）。
    """
    text = event.message.text.strip()
    url = (
        text
        .replace("下載影片", "")
        .replace("下載音訊", "")
        .replace("下載音樂", "")
        .strip()
    )

    if not url.lower().startswith("http"):
        api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text="❌ 請提供正確的 YouTube 連結。")]
        ))
        return

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "format": "bestaudio/best" if media_type == "audio" else "bestvideo+bestaudio/best"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = clean_title(info.get("title", "影片"))
            formats = info.get("formats") or [info]
            download_url = None

            for f in formats:
                mime = f.get("mime_type", "")
                direct_url = f.get("url")
                if direct_url and (
                    ("video/mp4" in mime and media_type == "video") or
                    ("audio/mp4" in mime and media_type == "audio")
                ):
                    download_url = direct_url
                    break

        if not download_url:
            raise ValueError("找不到可用的 direct 連結")

        api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(
                text=(
                    f"✅ 以下是「{title}」的 direct 連結：\n"
                    f"👉 請用瀏覽器開啟或另存：\n{download_url}"
                )
            )]
        ))

    except Exception as e:
        print("[handle_youtube_download] Error:", e)
        api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text="❌ 抱歉，無法擷取下載連結，請稍後再試。")]
        ))
