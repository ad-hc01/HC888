# -*- coding: utf-8 -*-
# 語音輸入模組（STT），將 LINE 語音訊息轉為文字

import tempfile
from openai import OpenAI, OpenAIError
from linebot.v3.messaging import MessagingApi, GetMessageContentRequest

# 初始化 OpenAI 客戶端
client = OpenAI()

def transcribe_audio_from_line(message_id: str, api: MessagingApi) -> str | None:
    """
    下載 LINE 語音訊息並使用 Whisper 轉錄為文字。
    :param message_id: LINE 訊息 ID
    :param api: 已初始化的 MessagingApi 實例
    :return: 轉錄文字，失敗回傳 None
    """
    try:
        # 1. 下載語音內容
        req = GetMessageContentRequest(message_id=message_id)
        resp = api.get_message_content(req)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            for chunk in resp.iter_bytes():
                tmp.write(chunk)
            tmp.flush()
            path = tmp.name

        # 2. Whisper 轉錄
        with open(path, "rb") as audio_file:
            result = client.audio.transcribe("whisper-1", audio_file)

        # 3. 回傳文字
        return result["text"] if isinstance(result, dict) else result.text
    except OpenAIError as e:
        print(f"[transcribe_audio_from_line] OpenAI error: {e}")
    except Exception as e:
        print(f"[transcribe_audio_from_line] Unexpected error: {e}")
    return None
