# -*- coding: utf-8 -*-
# 語音輸出模組（TTS），將文字轉為音訊並回傳 LINE AudioMessage

import os
import tempfile
from openai import OpenAI, OpenAIError
from linebot.v3.messaging import AudioMessage as V3AudioMessage, TextMessage as V3TextMessage

# 初始化 OpenAI 客戶端
client = OpenAI()

def upload_to_temp_url(filepath: str) -> str:
    """
    模擬將檔案上傳至公開 URL，請替換為實際雲端儲存實作。
    """
    filename = os.path.basename(filepath)
    return f"https://your-cdn.com/audio/{filename}"

def generate_tts_audio(text: str, user_id: str):
    """
    將文字轉為語音，回傳 V3AudioMessage；失敗則回傳文字訊息。
    """
    try:
        # 1. 呼叫 OpenAI TTS
        resp = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        # 2. 寫入暫存檔
        tmp_path = os.path.join(tempfile.gettempdir(), f"{user_id}_tts.mp3")
        with open(tmp_path, "wb") as f:
            f.write(resp.content)

        # 3. 上傳並取得公開 URL
        url = upload_to_temp_url(tmp_path)

        # 4. 回傳 LINE AudioMessage（duration 可自行計算或省略）
        return V3AudioMessage(
            original_content_url=url,
            duration=0
        )
    except OpenAIError as e:
        print(f"[generate_tts_audio] OpenAI error: {e}")
    except Exception as e:
        print(f"[generate_tts_audio] Unexpected error: {e}")

    return V3TextMessage(text="⚠️ TTS 產生失敗，請稍後再試。")
