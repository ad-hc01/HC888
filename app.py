# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 使用者命名記憶 
# + 翻譯 + YouTube 下載連結 + 地圖/抽卡/天氣 + 圖片風格生成 + 梅花易數 + 喚醒式安靜模式

import os
import unicodedata
from collections import defaultdict, deque
from datetime import date
from flask import Flask, request, abort

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage as V3TextMessage,
    ImageMessage as V3ImageMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    AudioMessageContent
)
from linebot.v3.exceptions import InvalidSignatureError

# —— 新增：年齡與人物資訊處理模組 ——
from age_handler import is_age_query, handle_age_query
from info_handler import (
    is_who_query, handle_who_query,
    is_birthday_query, handle_birthday_query,
    is_general_info_query, handle_general_info_query
)

# —— 既有模組匯入 ——
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
from image_analyzer import analyze_image_with_gpt
from image_generator_style import generate_stylized_image
from youtube_handler import search_youtube_card
from youtube_downloader import handle_youtube_download
from transport import get_thsr_schedule
from search_web import search_all_sources
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot
from weather_handler import get_weather_by_location
from extended_modules.map_handler import generate_map_image
from extended_modules.tts_handler import generate_tts_audio
from extended_modules.stt_handler import transcribe_audio_from_line
from meihua_handler import generate_meihua_hexagram

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
            user_id = event.source.user_id
            memory = user_data[user_id]
            try:
                profile = api.get_profile(user_id)
                memory["display_name"] = profile.display_name
            except:
                pass

            # —— 只處理文字訊息 ——  
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                text = event.message.text.strip()

                # 💤 安靜模式：先喚醒
                if user_id not in activated_users:
                    if memory["ai_name"].lower() in normalize_text(text):
                        activated_users.add(user_id)
                        memory["has_welcomed"] = True
                        welcome = (
                            f"嗨～我是你專屬助理 {memory['ai_name']} 😊\n"
                            "之後你可以直接講話，不用再說 HC 也會理你喔！"
                        )
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text=welcome)]
                        ))
                    continue  # 未喚醒前不處理其他

                # —— 基本設定／記憶管理 ——  
                if is_clear_facts(text):
                    memory["facts"].clear()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text="🧹 已清除你的個人知識。")]
                    ))
                    continue
                if fact := extract_user_fact(text):
                    memory["facts"].append(fact)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"📌 已記住：「{fact}」")]
                    ))
                    continue
                if new_name := extract_user_name(text):
                    memory["name"] = new_name
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"好的，我會叫你 {new_name}！")]
                    ))
                    continue
                if new_ai := extract_ai_name(text):
                    memory["ai_name"] = new_ai
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"從現在起，我就叫 {new_ai} 囉！")]
                    ))
                    continue
                if new_style := extract_user_style(text):
                    memory["style"] = new_style
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"已切換為「{new_style}」風格。")]
                    ))
                    continue

                # —— 翻譯流程 ——  
                if memory["translate_pending"]:
                    original = memory.pop("translate_pending")
                    translated = translate_text(original, text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=f"翻譯成「{text}」結果：\n{original} → {translated}")]
                    ))
                    continue
                if is_translate_request(text):
                    memory["translate_pending"] = text.replace("翻譯", "").strip()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text="你想翻譯成哪一種語言呢？")]
                    ))
                    continue

                # —— 媒體／功能模組 ——  
                if text.startswith("下載影片"):
                    handle_youtube_download(event, api, media_type="video"); continue
                if text.startswith("下載音訊") or text.startswith("下載音樂"):
                    handle_youtube_download(event, api, media_type="audio"); continue

                if is_stylegen_request(text):
                    memory["user_pending_stylegen"] = text.replace("幫我生成", "").replace("風格", "").strip()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text="請傳一張圖片給我套用風格～")]
                    ))
                    continue

                if is_image_request(text):
                    msg = generate_image_message(text)
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg])); continue

                if is_video_request(text):
                    msg = search_youtube_card(text)
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg])); continue

                if is_transport_request(text):
                    msg = get_thsr_schedule()
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg])); continue

                if is_draw_request(text):
                    out = draw_tarot() if "塔羅" in text.lower() else draw_fortune()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=out)]
                    )); continue

                if is_meihua_request(text):
                    out = generate_meihua_hexagram()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=out)]
                    )); continue

                if is_map_request(text):
                    out = generate_map_image(text)
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[out])); continue

                if is_weather_request(text):
                    out = get_weather_by_location(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=out)]
                    )); continue

                # —— 新增：各類查詢攔截 ——  
                # 1. 年齡查詢
                if is_age_query(text):
                    reply = handle_age_query(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                    continue
                # 2. 是誰查詢
                if is_who_query(text):
                    reply = handle_who_query(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                    continue
                # 3. 生日查詢
                if is_birthday_query(text):
                    reply = handle_birthday_query(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                    continue
                # 4. 通用屬性查詢
                if is_general_info_query(text):
                    reply = handle_general_info_query(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                    continue

                # —— 其他問題 ——  
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

                memory["history"].append({"role": "user", "content": text})
                memory["history"].append({"role": "assistant", "content": reply})
                user_label = memory["display_name"] or memory["name"] or "朋友"
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"{user_label}～{reply}")]
                ))

            # —— 圖片／音訊處理 ——  
            if isinstance(event, MessageEvent) and isinstance(event.message, ImageMessageContent):
                if style := memory.get("user_pending_stylegen"):
                    memory["user_pending_stylegen"] = None
                    src = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"
                    styled = generate_stylized_image(src, style)
                    if styled:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3ImageMessage(
                                original_content_url=styled,
                                preview_image_url=styled
                            )]
                        ))
                    else:
                        api.reply_message(ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[V3TextMessage(text="❌ 圖片風格生成失敗")]
                        ))
                    continue

                analysis = analyze_image_with_gpt(
                    message_id=event.message.id,
                    api=api,
                    user_name=memory["name"],
                    ai_name=memory["ai_name"],
                    style=memory["style"]
                )
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=analysis)]
                ))
                continue

            if isinstance(event, MessageEvent) and isinstance(event.message, AudioMessageContent):
                transcript = transcribe_audio_from_line(event.message.id, api)
                if transcript:
                    reply = generate_gpt_reply(
                        user_id=user_id,
                        user_msg=transcript,
                        history=memory["history"],
                        user_name=memory["name"],
                        ai_name=memory["ai_name"],
                        style=memory["style"],
                        facts=memory["facts"]
                    )
                    memory["history"].append({"role": "user", "content": transcript})
                    memory["history"].append({"role": "assistant", "content": reply})
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=reply)]
                    ))
                continue

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
