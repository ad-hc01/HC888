# -*- coding: utf-8 -*-
# 本檔案為主控程式，整合 GPT 導師 + 多模組 + 使用者命名記憶 
# + 翻譯 + YouTube 下載連結 + 地圖/抽卡/天氣 + 圖片風格生成

import os
import unicodedata
from collections import defaultdict, deque
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
from linebot.v3.messaging.models import GetProfileRequest
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    AudioMessageContent
)
from linebot.v3.exceptions import InvalidSignatureError

from utils import (
    extract_user_name, extract_ai_name, extract_user_style,
    extract_user_fact, is_clear_facts,
    is_image_request, is_video_request, is_transport_request,
    is_map_request, is_translate_request,
    is_draw_request, is_weather_request, is_stylegen_request
)
from gpt_handler import generate_gpt_reply
from image_generator import generate_image_message
from image_analyzer import analyze_image_with_gpt
from image_generator_style import generate_stylized_image
from youtube_handler import search_youtube_card
from youtube_downloader import handle_youtube_download
from transport import get_thsr_schedule
from search_web import search_web_fallback
from translate_handler import translate_text
from draw_handler import draw_fortune, draw_tarot, draw_custom
from weather_handler import get_weather_by_location
from extended_modules.map_handler import generate_map_image
from extended_modules.tts_handler import generate_tts_audio
from extended_modules.stt_handler import transcribe_audio_from_line

app = Flask(__name__)
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))
cfg = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# 使用者記憶結構
user_data = defaultdict(lambda: {
    "name": None,
    "display_name": None,
    "ai_name": "HC",
    "style": "正式風",
    "history": deque(maxlen=20),
    "facts": [],
    "translate_pending": None,
    "user_pending_stylegen": None,
    "has_welcomed": False
})

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

            # 更新用戶顯示名稱
            try:
                profile = api.get_profile(GetProfileRequest(user_id=user_id))
                memory["display_name"] = profile.display_name
            except Exception:
                pass

            # 處理文字訊息
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                text = event.message.text.strip()

                # 清除知識／記住事實／改名／切換風格
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

                # 翻譯
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

                # YouTube 下載
                if text.startswith("下載影片"):
                    handle_youtube_download(event, api, media_type="video")
                    continue
                if text.startswith("下載音訊") or text.startswith("下載音樂"):
                    handle_youtube_download(event, api, media_type="audio")
                    continue

                # 觸發 AI 回應
                ai_name = memory["ai_name"] or "HC"
                if normalize_text(ai_name) not in normalize_text(text):
                    continue
                if not memory["has_welcomed"]:
                    memory["has_welcomed"] = True
                    welcome = (
                        f"嗨～我是你專屬助理 {ai_name} 😊\n"
                        "我會記住你說過的 20 句話，隨時叫我「" + ai_name + "」就可以開始對話！"
                    )
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=welcome)]
                    ))
                    continue

                # 單一模組指令
                if is_stylegen_request(text):
                    memory["user_pending_stylegen"] = text.replace("幫我生成", "").replace("風格", "").strip()
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text="請傳一張圖片給我套用風格～")]
                    ))
                    continue
                if is_image_request(text):
                    msg = generate_image_message(text)
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg]))
                    continue
                if is_video_request(text):
                    msg = search_youtube_card(text)
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg]))
                    continue
                if is_transport_request(text):
                    msg = get_thsr_schedule()
                    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg]))
                    continue
                if is_draw_request(text):
                    if "運勢" in text:
                        out = draw_fortune()
                    elif "塔羅" in text.lower():
                        out = draw_tarot()
                    else:
                        pool = text.split("抽")[-1].strip().split("、")
                        out = draw_custom(pool)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=out)]
                    ))
                    continue
                if is_map_request(text):
                    out = generate_map_image(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[out]
                    ))
                    continue
                if is_weather_request(text):
                    out = get_weather_by_location(text)
                    api.reply_message(ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[V3TextMessage(text=out)]
                    ))
                    continue

                # GPT 回應
                reply = generate_gpt_reply(
                    user_id=user_id,
                    user_msg=text,
                    history=memory["history"],
                    user_name=memory["name"],
                    ai_name=memory["ai_name"],
                    style=memory["style"],
                    facts=memory["facts"]
                )
                if any(kw in reply for kw in ["我不知道", "無法提供"]):
                    reply += "\n\n" + search_web_fallback(text)
                memory["history"].append({"role": "user", "content": text})
                memory["history"].append({"role": "assistant", "content": reply})
                user_label = memory["display_name"] or memory["name"] or "朋友"
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[V3TextMessage(text=f"{user_label}～{reply}")]
                ))
                continue

            # 處理圖片訊息
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

            # 處理語音訊息
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
