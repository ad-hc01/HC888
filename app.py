# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 使用者命名記憶 
# + 翻譯 + YouTube 下載連結 + 地圖/抽卡/天氣 + 圖片風格生成 + 梅花易數 + 喚醒式安靜模式

import os
import unicodedata
from collections import defaultdict, deque
from flask import Flask, request, abort

# —— 通用查詢模組 ——  
from info_handler import (
    is_time_query, handle_time_query,
    is_age_query, handle_age_query,
    is_who_query, handle_who_query,
    is_birthday_query, handle_birthday_query,
    is_debut_query, handle_debut_query,
    is_album_query, handle_album_query,
    is_general_info_query, handle_general_info_query
)

# LINE SDK
from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage as V3TextMessage, ImageMessage as V3ImageMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, AudioMessageContent
from linebot.v3.exceptions import InvalidSignatureError

# 各項功能模組
from utils import (
    extract_user_name, extract_ai_name, extract_user_style,
    extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request,
    is_map_request, is_translate_request,
    is_draw_request, is_weather_request, is_stylegen_request,
    is_meihua_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_message
from image_generator_style import generate_stylized_image
from youtube_handler import search_youtube_card
from youtube_downloader import handle_youtube_download
from transport import get_thsr_schedule
from search_web import search_all_sources
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot
from weather_handler import get_weather_by_location
from extended_modules.map_handler import generate_map_image
from extended_modules.stt_handler import transcribe_audio_from_line
from meihua_handler import generate_meihua_hexagram

app = Flask(__name__)
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))
cfg = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# 使用者記憶結構
user_data = defaultdict(lambda: {
    "name": None,
    "display_name": None,
    "ai_name": "HC",
    "style": "正式風",
    "history": deque(maxlen=50),
    "facts": [],
    "translate_pending": None,
    "user_pending_stylegen": None,
    "has_welcomed": False
})
activated_users = set()

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKC', text).lower()

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    with ApiClient(cfg) as client:
        api = MessagingApi(client)

        for event in events:
            if not isinstance(event, MessageEvent):
                continue

            user_id = getattr(event.source, "user_id", None)
            memory = user_data[user_id]

            # 嘗試更新顯示名稱
            try:
                profile = api.get_profile(user_id)
                memory["display_name"] = profile.display_name
            except:
                pass

            # 處理文字或音訊
            if isinstance(event.message, TextMessageContent) or isinstance(event.message, AudioMessageContent):
                # 若為音訊，先 STT
                if isinstance(event.message, AudioMessageContent):
                    try:
                        text = transcribe_audio_from_line(event.message.id) or ""
                    except Exception as e:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text=f"⚠️ 音訊轉文字失敗：{e}")]
                        ))
                        continue
                else:
                    text = event.message.text.strip()

                # 喚醒式安靜模式
                if user_id not in activated_users:
                    if memory["ai_name"].lower() in normalize_text(text):
                        activated_users.add(user_id)
                        memory["has_welcomed"] = True
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(
                                text=f"嗨～我是你專屬助理 {memory['ai_name']} 😊\n以後直接講即可，不用再說 HC！"
                            )]
                        ))
                    continue

                # 依序判斷各功能
                try:
                    if is_time_query(text):
                        reply = handle_time_query()
                    elif is_age_query(text):
                        reply = handle_age_query(text)
                    elif is_who_query(text):
                        reply = handle_who_query(text)
                    elif is_birthday_query(text):
                        reply = handle_birthday_query(text)
                    elif is_debut_query(text):
                        reply = handle_debut_query(text)
                    elif is_album_query(text):
                        reply = handle_album_query(text)
                    elif is_general_info_query(text):
                        reply = handle_general_info_query(text)
                    elif is_clear_facts(text):
                        memory["facts"].clear()
                        reply = "🧹 已清除你的個人知識。"
                    elif fact := extract_user_fact(text):
                        memory["facts"].append(fact)
                        reply = f"📌 已記住：「{fact}」"
                    elif new_name := extract_user_name(text):
                        memory["name"] = new_name
                        reply = f"好的，我會叫你 {new_name}！"
                    elif new_ai := extract_ai_name(text):
                        memory["ai_name"] = new_ai
                        reply = f"從現在起，我就叫 {new_ai}！"
                    elif new_style := extract_user_style(text):
                        memory["style"] = new_style
                        reply = f"已切換為「{new_style}」風格。"
                    elif memory["translate_pending"]:
                        original = memory.pop("translate_pending")
                        translated = translate_text(original, text)
                        reply = f"翻譯結果：\n{original} → {translated}"
                    elif text.startswith("翻譯"):
                        memory["translate_pending"] = text.replace("翻譯", "").strip()
                        reply = "你想翻譯成哪一種語言呢？"
                    elif text.startswith("下載影片") or text.startswith("下載音訊") or text.startswith("下載音樂"):
                        handle_youtube_download(event, api,
                                                media_type="audio" if "音" in text else "video")
                        continue
                    elif is_stylegen_request(text):
                        memory["user_pending_stylegen"] = text.replace("幫我生成", "").replace("風格", "").strip()
                        reply = "請傳一張圖片給我套用風格～"
                    else:
                        reply = generate_gpt_reply(
                            user_id=user_id,
                            user_msg=text,
                            history=memory["history"],
                            user_name=memory["name"],
                            ai_name=memory["ai_name"],
                            style=memory["style"],
                            facts=memory["facts"]
                        )
                        if any(k in reply for k in ["我不知道", "無法提供", "不確定", "請自行查"]):
                            reply += "\n\n" + search_all_sources(text)
                except Exception as e:
                    reply = f"⚠️ 處理失敗：{e}"

                # 紀錄對話並回覆
                memory["history"].append({"role": "user", "content": text})
                memory["history"].append({"role": "assistant", "content": reply})
                label = memory["display_name"] or memory["name"] or "朋友"
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"{label}：{reply}")]
                ))
                continue
            # 處理圖片：風格化優先，否則一般生成
            if isinstance(event.message, ImageMessageContent):
                try:
                    if style := memory.get("user_pending_stylegen"):
                        memory["user_pending_stylegen"] = None
                        src = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"
                        styled = generate_stylized_image(src, style)
                        if styled:
                            msg = V3ImageMessage(
                                original_content_url=styled,
                                preview_image_url=styled
                            )
                        else:
                            msg = V3TextMessage(text="❌ 圖片風格生成失敗")
                    elif is_image_request(memory["history"][-1]["content"]):
                        msg = generate_image_message(memory["history"][-1]["content"])
                    else:
                        continue

                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[msg]
                    ))
                except Exception as e:
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"⚠️ 圖片處理失敗：{e}")]
                    ))
                continue

    # 統一回傳 OK
    return "OK", 200


if __name__ == "__main__":
    # 讀取 Render 指定的 PORT（預設 5000），並綁定到 0.0.0.0
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
