# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 使用者命名記憶 
# + 翻譯 + YouTube 下載連結 + 地圖/抽卡/天氣 + 圖片風格生成 + 梅花易數 + 喚醒式安靜模式 + 圖片生成 + 圖像分析 + 語音回話（AI自動說話）

import os
import unicodedata
from collections import defaultdict, deque
from flask import Flask, request, abort

from info_handler import (
    is_time_query, handle_time_query,
    is_age_query, handle_age_query,
    is_who_query, handle_who_query,
    is_birthday_query, handle_birthday_query,
    is_debut_query, handle_debut_query,
    is_album_query, handle_album_query,
    is_general_info_query, handle_general_info_query
)

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage as V3TextMessage, ImageMessage as V3ImageMessage,
    AudioMessage as V3AudioMessage, PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, AudioMessageContent
from linebot.v3.exceptions import InvalidSignatureError

from utils import (
    extract_user_name, extract_ai_name, extract_user_style,
    extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request,
    is_map_request, is_translate_request,
    is_draw_request, is_weather_request, is_stylegen_request,
    is_imagegen_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_from_prompt, generate_image_message
from image_generator_style import generate_stylized_image
from prompt_enhancer import enhance_prompt_with_style
from youtube_handler import search_youtube_card
from youtube_downloader import handle_youtube_download
from transport import get_thsr_schedule
from search_web import search_all_sources
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot
from weather_handler import get_weather_by_location
from extended_modules.map_handler import generate_map_image
from extended_modules.stt_handler import transcribe_audio_from_line
from extended_modules.tts_handler import generate_tts_audio
from meihua_handler import generate_meihua_hexagram
from realtime_monitor import start_monitor, stop_monitor, get_monitor_status
from image_analyzer import analyze_image_with_gpt

app = Flask(__name__)
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))
cfg = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
user_data = defaultdict(lambda: {
    "name": None,
    "display_name": None,
    "ai_name": "HC",
    "style": "正式風",
    "history": deque(maxlen=50),
    "facts": [],
    "translate_pending": None,
    "user_pending_stylegen": None,
    "has_welcomed": False,   # ← 補這個逗號
    "voice": "nova"
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

            try:
                profile = api.get_profile(user_id)
                memory["display_name"] = profile.display_name
            except:
                pass

            # 這一段，**全都要縮排到 for 迴圈內！**
            if isinstance(event.message, TextMessageContent) or isinstance(event.message, AudioMessageContent):
                if isinstance(event.message, AudioMessageContent):
                    try:
                        text = transcribe_audio_from_line(event.message.id) or ""
                        if not text:
                            raise Exception("轉錄結果為空")

                        reply = generate_gpt_reply(
                            user_id=user_id,
                            user_msg=text,
                            history=memory["history"],
                            user_name=memory["name"],
                            ai_name=memory["ai_name"],
                            style=memory["style"],
                            facts=memory["facts"]
                        )
                        memory["history"].append({"role": "user", "content": text})
                        memory["history"].append({"role": "assistant", "content": reply})

                        voice = memory.get("voice", "nova")
                        voice_msg = generate_tts_audio(reply, voice)
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[voice_msg]
                        ))
                        continue

                    except Exception as e:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text=f"⚠️ 音訊處理錯誤：{e}")]  # LINE 會自動轉 UTF8
                        ))
                        continue
                else:
                    text = event.message.text.strip()
            # ...後面請維持原本的縮排...


            if user_id not in activated_users:
                if memory["ai_name"].lower() in normalize_text(text):
                    activated_users.add(user_id)
                    memory["has_welcomed"] = True
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(
                            text=f"嗨～我是你專屬助理 {memory['ai_name']} 😊\n以後直接說即可，不用再說 HC！"
                        )]
                    ))
                    continue

            if is_imagegen_request(text):
                try:
                    prompt = enhance_prompt_with_style(text)
                    image_url = generate_image_from_prompt(prompt)

                    if image_url.startswith("http"):
                        msg = V3ImageMessage(
                            original_content_url=image_url,
                            preview_image_url=image_url
                        )
                    else:
                        msg = V3TextMessage(text=image_url)

                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[msg]
                    ))
                except Exception as e:
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"⚠️ 圖片生成錯誤：{e}")]
                    ))
                continue

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
                elif text.strip() == "@顯示使用者ID":
                    uid = getattr(event.source, "user_id", None)
                    admin_uid = os.getenv("LINE_ADMIN_USER")
                    reply = f"👤 你的使用者 ID 是：\n{uid}" if uid == admin_uid else "🚫 無權查看使用者 ID。"
                elif text.strip() == "@顯示群組ID":
                    gid = getattr(event.source, "group_id", None)
                    admin_uid = os.getenv("LINE_ADMIN_USER")
                    reply = f"👥 此群組 ID 是：\n{gid}" if user_id == admin_uid else "🚫 無權查看群組 ID。"
                elif text.strip() == "@顯示來源ID":
                    src = getattr(event.source, "group_id", None) or getattr(event.source, "user_id", None)
                    admin_uid = os.getenv("LINE_ADMIN_USER")
                    reply = f"🔐 目前來源 ID 是：\n{src}" if user_id == admin_uid else "🚫 無權查看來源 ID。"

                elif text.startswith("聲音模式:"):
                    voice_choice = text.replace("聲音模式:", "").strip().lower()
                    if voice_choice in ["nova", "shimmer", "echo", "fable", "onyx"]:
                        memory["voice"] = voice_choice
                        reply = f"✅ 已切換語音模式為「{voice_choice}」"
                    else:
                        reply = "⚠️ 語音模式錯誤，請使用：nova、shimmer、echo、fable、onyx"

                elif text.startswith("啟動監聽:"):
                    raw = text.replace("啟動監聽:", "").strip()
                    reply = start_monitor(raw, getattr(event.source, "group_id", None) or event.source.user_id, api)
                elif text == "停止監聽":
                    reply = stop_monitor()
                elif text == "監聽狀態":
                    reply = get_monitor_status()

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

            memory["history"].append({"role": "user", "content": text})
            memory["history"].append({"role": "assistant", "content": reply})
            label = memory["display_name"] or memory["name"] or "朋友"
            api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=f"{label}：{reply}")]
            ))
            continue  # ✅ 這裡保留，結束 Text 處理迴圈

        # ✅ 圖片處理：搬出 try 外，才能被執行
        if isinstance(event.message, ImageMessageContent):
            try:
                src = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"

                if style := memory.get("user_pending_stylegen"):
                    memory["user_pending_stylegen"] = None
                    styled = generate_stylized_image(src, style)
                    if styled:
                        msg = V3ImageMessage(
                            original_content_url=styled,
                            preview_image_url=styled
                        )
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[msg]
                        ))
                    else:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text="❌ 圖片風格生成失敗")]
                        ))
                else:
                    msgs = analyze_image_with_gpt(
                        event.message.id,
                        api,
                        memory["name"],
                        memory["ai_name"],
                        memory["style"]
                    )
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=msgs
                    ))
            except Exception as e:
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"⚠️ 圖片處理失敗：{e}")]
                ))


    return "OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
