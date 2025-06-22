# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 固定 AI 名稱 + 群組需 @ 才啟動回應 + 私聊自動對話 + 每人記憶上限 50 句（含 debug）

import os
import unicodedata
from flask import Flask, request, abort
from collections import defaultdict, deque

from linebot.v3.messaging import (
    MessagingApi, TextMessage as V3TextMessage,
    ReplyMessageRequest
)
from linebot.v3.webhook import WebhookHandler as V3WebhookHandler
from linebot.v3.messaging.configuration import Configuration
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
from linebot.v3.webhook.models import SourceGroup, SourceUser  # ✅ 補 SourceUser

from utils import (
    extract_user_name, extract_user_style, extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request, is_map_request,
    is_translate_request, is_draw_request, is_weather_request, is_stylegen_request,
    is_help_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_message
from image_analyzer import analyze_image_with_gpt
from image_generator_style import generate_stylized_image
from transport import get_thsr_schedule, get_tra_schedule, get_flight_schedule
from search_web import search_web_fallback
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot, draw_custom
from weather_handler import get_weather_by_location
from extended_modules.map_handler import generate_map_image
from extended_modules.youtube_search import search_youtube_flex

app = Flask(__name__)
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(configuration)
handler = V3WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

BOT_NAME = "HC-GPT智能小幫手"
MAX_HISTORY = 50

user_data = defaultdict(lambda: {
    "name": None,
    "display_name": None,
    "style": "正式風",
    "history": deque(maxlen=MAX_HISTORY),
    "facts": [],
    "translate_pending": None,
    "user_pending_stylegen": None,
    "enabled": False
})

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/", methods=["GET"])
def home():
    return "🤖 HC-GPT智能小幫手上線中！"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    try:
        text = event.message.text.strip()
        print(f"[debug] 收到訊息：{text}")

        source = event.source
        user_id = getattr(source, "user_id", None) or getattr(source, "group_id", None) or getattr(source, "room_id", None) or "unknown"

        memory = user_data.setdefault(user_id, {
            "name": None,
            "display_name": None,
            "style": "正式風",
            "history": deque(maxlen=MAX_HISTORY),
            "facts": [],
            "translate_pending": None,
            "user_pending_stylegen": None,
            "enabled": False
        })

        is_group = isinstance(source, SourceGroup)
        is_user = isinstance(source, SourceUser)
        mentioned = f"@{BOT_NAME}" in text

        if is_group:
            if mentioned:
                memory["enabled"] = True
                memory["history"].clear()
                print("[debug] 群組啟用")
            elif not memory["enabled"]:
                print("[debug] 群組未啟用，略過")
                return
            elif len(memory["history"]) >= MAX_HISTORY:
                memory["enabled"] = False
                print("[debug] 群組歷史超過限制，自動關閉")
                return

        print(f"[debug] 使用者 ID: {user_id}")

        if is_help_request(text):
            reply = (
                f"📌 我是 {BOT_NAME}，支援功能如下：\n"
                "- GPT 回答 / 記憶功能\n"
                "- 翻譯：輸入「翻譯 xxx」\n"
                "- 圖像風格化：幫我生成 xxx風格\n"
                "- 地圖查詢 / 天氣查詢\n"
                "- 抽卡（運勢、塔羅、自訂）\n"
                "- YouTube 搜尋\n"
                "- 台鐵 / 高鐵 / 航班查詢\n"
                "- 語氣風格切換 / 命名\n"
                "- 清空知識：「清空知識」"
            )
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_clear_facts(text):
            memory["facts"] = []
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text="🧹 已清除你的個人知識。")]
            ))
            return

        if (fact := extract_user_fact(text)):
            memory["facts"].append(fact)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=f"📌 已記住：「{fact}」")]
            ))
            return

        if (new_name := extract_user_name(text)):
            memory["name"] = new_name
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=f"好的，我會叫你 {new_name}！")]
            ))
            return

        if (new_style := extract_user_style(text)):
            memory["style"] = new_style
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=f"已切換為「{new_style}」風格。")]
            ))
            return

        if memory["translate_pending"]:
            original = memory["translate_pending"]
            target_lang = text.strip()
            translated = translate_text(original, target_lang)
            memory["translate_pending"] = None
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=f"翻譯成「{target_lang}」結果如下：\n{original} → {translated}")]
            ))
            return

        if is_translate_request(text):
            original_text = text.replace("翻譯", "").strip()
            memory["translate_pending"] = original_text
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text="你想翻譯成哪一種語言呢？例如英文、日文、韓文、法文...")]
            ))
            return

        if is_video_request(text):
            reply = search_youtube_flex(text)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_stylegen_request(text):
            style = text.replace("幫我生成", "").replace("風格", "").strip()
            memory["user_pending_stylegen"] = style
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text="請傳一張圖片，我會幫你套上風格～")]
            ))
            return

        if is_image_request(text):
            reply = generate_image_message(text)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_transport_request(text):
            if "高鐵" in text:
                reply = get_thsr_schedule(text)
            elif "台鐵" in text:
                reply = get_tra_schedule(text)
            elif "航班" in text or "飛機" in text:
                reply = get_flight_schedule(text)
            else:
                reply = "請說明要查詢 高鐵、台鐵 或 航班"
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_draw_request(text):
            if "運勢" in text:
                reply = draw_fortune()
            elif "塔羅" in text or "tarot" in text.lower():
                reply = draw_tarot()
            elif "自訂" in text and "抽" in text:
                pool = text.split("抽")[-1].strip().split("、")
                reply = draw_custom(pool)
            else:
                reply = "請指定要抽的類型，例如「抽運勢」、「抽塔羅」、「抽蘋果、香蕉、葡萄」"
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_map_request(text):
            reply = generate_map_image(text)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        if is_weather_request(text):
            reply = get_weather_by_location(text)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[V3TextMessage(text=reply)]
            ))
            return

        reply = generate_gpt_reply(
            user_id=user_id,
            user_msg=text,
            history=memory["history"],
            user_name=memory["name"],
            ai_name=BOT_NAME,
            style=memory["style"],
            facts=memory["facts"]
        )
        if "我不知道" in reply or "無法提供" in reply:
            reply += f"\n\n{search_web_fallback(text)}"

        memory["history"].append({"role": "user", "content": text})
        memory["history"].append({"role": "assistant", "content": reply})

        display = memory["display_name"] or memory["name"] or "朋友"
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text=f"{display}～{reply}")]
        ))

    except Exception as e:
        print(f"[❌ handle_text error] {e}")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        source = event.source
        user_id = getattr(source, "user_id", None) or getattr(source, "group_id", None) or "unknown"

        memory = user_data.setdefault(user_id, {
            "name": None,
            "display_name": None,
            "style": "正式風",
            "history": deque(maxlen=MAX_HISTORY),
            "facts": [],
            "translate_pending": None,
            "user_pending_stylegen": None,
            "enabled": False
        })

        message_id = event.message.id
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"

        if memory.get("user_pending_stylegen"):
            style = memory.pop("user_pending_stylegen")
            styled_url = generate_stylized_image(image_url, style)
            if styled_url:
                line_bot_api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"✅ 已完成風格轉換：\n{styled_url}")]
                ))
            else:
                line_bot_api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text="❌ 圖片風格生成失敗")]
                ))
            return

        reply = analyze_image_with_gpt(message_id, line_bot_api, memory["name"], BOT_NAME, memory["style"])
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text=reply)]
        ))
    except Exception as e:
        print(f"[❌ handle_image error] {e}")
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[V3TextMessage(text=f"⚠️ 圖片處理錯誤：{e}")]
        ))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
