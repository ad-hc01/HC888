# -*- coding: utf-8 -*-
# 語音輸入模組（STT），將 LINE 語音訊息轉為文字

import os
import tempfile
import requests
from openai import OpenAI, OpenAIError

# 初始化 OpenAI 客戶端（自動讀取 OPENAI_API_KEY）
client = OpenAI()

# LINE 音訊下載網址格式
CONTENT_URL = "https://api-data.line.me/v2/bot/message/{message_id}/content"

def transcribe_audio_from_line(message_id: str) -> str | None:
    """
    下載 LINE 音訊並使用 OpenAI Whisper 模型轉文字。
    :param message_id: LINE 語音訊息 ID
    :return: 認出來的語音文字（失敗回傳 None）
    """
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return None

    url = CONTENT_URL.format(message_id=message_id)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. 下載音訊內容
        resp = requests.get(url, headers=headers, timeout=10.0)
        resp.raise_for_status()

        # 2. 儲存至暫存檔
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            tmp.write(resp.content)
            audio_path = tmp.name

        # 3. Whisper 語音辨識
        with open(audio_path, "rb") as f:
            result = client.audio.transcribe("whisper-1", f)

        # 4. 傳回辨識結果
        return result.get("text") if isinstance(result, dict) else result.text

    except (OpenAIError, Exception) as e:
        print(f"[transcribe_audio_from_line] 語音辨識錯誤: {e}")
        return None
