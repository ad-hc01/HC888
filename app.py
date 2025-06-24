# -*- coding: utf-8 -*-
import os
import unicodedata
from collections import defaultdict, deque
from flask import Flask, request, abort, url_for

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
    AudioMessage as V3AudioMessage
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent, AudioMessageContent
)
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
    "has_welcomed": False,
    "voice": "nova",
    "reply_mode": "auto"
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

            # ===== 1. 語音訊息處理 =====
            if isinstance(event.message, AudioMessageContent):
                try:
                    text = transcribe_audio_from_line(event.message.id) or ""
                    if not text:
                        raise Exception("轉錄結果為空")
                    memory["history"].append({"role": "user", "content": text})

                    reply = generate_gpt_reply(
                        user_id=user_id,
                        user_msg=text,
                        history=memory["history"],
                        user_name=memory["name"],
                        ai_name=memory["ai_name"],
                        style=memory["style"],
                        facts=memory["facts"]
                    )
                    memory["history"].append({"role": "assistant", "content": reply})

                    if memory.get("reply_mode") == "voice":
                        msg = generate_tts_audio(reply, memory.get("voice", "nova"))
                    else:
                        label = memory["display_name"] or memory["name"] or "朋友"
                        msg = V3TextMessage(text=f"{label}：{reply}")

                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[msg]
                    ))
                except Exception as e:
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"⚠️ 音訊處理錯誤：{e}")]
                    ))
                continue

            # ===== 2. 文字訊息處理 =====
            if isinstance(event.message, TextMessageContent):
                text = event.message.text.strip()

                # 回應模式設定
                if text.startswith("回應模式:"):
                    mode = text.split("回應模式:",1)[1].strip().lower()
                    if mode in ["auto","自動"]:
                        memory["reply_mode"] = "auto"
                        reply = "✅ 已切換為自動回應模式（語音問回語音，其它都回文字）"
                    elif mode in ["voice","語音"]:
                        memory["reply_mode"] = "voice"
                        reply = "✅ 已切換為語音回應模式（都回語音）"
                    elif mode in ["text","文字"]:
                        memory["reply_mode"] = "text"
                        reply = "✅ 已切換為純文字回應模式"
                    else:
                        reply = "⚠️ 指令錯誤，請用：回應模式:自動/語音/文字"
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                    continue

                # 語音播報
                if text.startswith("語音播報:"):
                    from extended_modules.tts_handler import generate_tts_file
                    tts_text = text.split("語音播報:", 1)[1].strip()
                    tts_fp = generate_tts_file(tts_text, memory.get("voice", "nova"))

                    if not tts_fp:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text="⚠️ 語音產生失敗，請稍後再試。")]
                        ))
                        continue

                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(tts_fp)
                        duration_ms = len(audio)
                    except ImportError:
                        duration_ms = 1000

                    url = request.url_root.rstrip("/") + url_for("serve_audio", filename=os.path.basename(tts_fp))
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3AudioMessage(original_content_url=url, duration=duration_ms)]
                    ))
                    continue

                # 激活 HC
                if user_id not in activated_users and memory["ai_name"].lower() in normalize_text(text):
                    activated_users.add(user_id)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"嗨～我是你專屬助理 {memory['ai_name']} 😊")]
                    ))
                    continue

                # AI 繪圖
                if is_imagegen_request(text):
                    try:
                        prompt = enhance_prompt_with_style(text)
                        img_url = generate_image_from_prompt(prompt)
                        msg = V3ImageMessage(original_content_url=img_url, preview_image_url=img_url) if img_url.startswith("http") else V3TextMessage(text=img_url)
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

                # 其他功能
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
                        orig = memory.pop("translate_pending")
                        trans = translate_text(orig, text)
                        reply = f"翻譯結果：\n{orig} → {trans}"
                    elif text.startswith("翻譯"):
                        memory["translate_pending"] = text.split("翻譯",1)[1].strip()
                        reply = "你想翻譯成哪一種語言呢？"
                    else:
                        reply = generate_gpt_reply(
                            user_id=user_id, user_msg=text,
                            history=memory["history"],
                            user_name=memory["name"], ai_name=memory["ai_name"],
                            style=memory["style"], facts=memory["facts"]
                        )
                except Exception as e:
                    reply = f"⚠️ 處理失敗：{e}"

                memory["history"].append({"role":"user","content":text})
                memory["history"].append({"role":"assistant","content":reply})
                label = memory["display_name"] or memory["name"] or "朋友"
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"{label}：{reply}")]
                ))
                continue

            # ===== 3. 圖片訊息處理 =====
            if isinstance(event.message, ImageMessageContent):
                try:
                    src = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"
                    if memory.get("user_pending_stylegen"):
                        style = memory.pop("user_pending_stylegen")
                        styled_url = generate_stylized_image(src, style)
                        msg = V3ImageMessage(original_content_url=styled_url, preview_image_url=styled_url)
                    else:
                        msgs = analyze_image_with_gpt(
                            event.message.id, api,
                            memory["name"], memory["ai_name"], memory["style"]
                        )
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=msgs
                        ))
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

    return "OK", 200

# ===== Flask 靜態路由 =====
@app.route('/audio/<filename>')
def serve_audio(filename):
    from flask import send_file
    return send_file(f'/tmp/{filename}', mimetype='audio/mp3')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
