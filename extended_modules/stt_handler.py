# -*- coding: utf-8 -*-
# 語音輸入模組（STT），將 LINE 語音訊息轉為文字
import os
import tempfile
import requests
from openai import OpenAI, OpenAIError

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

# LINE 內容下載 URL 模板
CONTENT_URL = "https://api-data.line.me/v2/bot/message/{message_id}/content"

def transcribe_audio_from_line(message_id: str) -> str | None:
    """
    下載 LINE 語音訊息並使用 Whisper 轉錄為文字。
    :param message_id: LINE 訊息 ID
    :return: 轉錄文字；失敗時回傳 None
    """
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return None

    url = CONTENT_URL.format(message_id=message_id)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. 下載音訊二進位
        resp = requests.get(url, headers=headers, timeout=10.0)
        resp.raise_for_status()
        data = resp.content

        # 2. 寫入暫存檔
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            tmp.write(data)
            tmp.flush()
            path = tmp.name

        # 3. Whisper 轉錄
        with open(path, "rb") as audio_file:
            result = client.audio.transcribe("whisper-1", audio_file)

        # 4. 回傳文字
        return result["text"] if isinstance(result, dict) else result.text

    except OpenAIError:
        # Whisper API 本身錯誤
        return None
    except Exception:
        # 包含 HTTP、IOError 等各類錯誤
        return None
