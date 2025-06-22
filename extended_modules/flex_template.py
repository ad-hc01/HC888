# -*- coding: utf-8 -*-
# 本檔案為互動式卡片模組，提供影片、地圖、推薦資訊等 Flex Message 建立工具

from linebot.v3.messaging import TextMessage as V3TextMessage, ImageMessage as V3ImageMessage FlexSendMessage

def create_video_card(title, description, thumbnail_url, video_url):
    """
    建立影片推薦卡片（含預覽圖、標題、說明、按鈕）
    """
    flex_content = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": thumbnail_url,
            "size": "full",
            "aspectRatio": "16:9",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {"type": "text", "text": title, "wrap": True, "weight": "bold", "size": "lg"},
                {"type": "text", "text": description, "wrap": True, "size": "sm", "color": "#666666"}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "action": {
                        "type": "uri",
                        "label": "▶️ 觀看影片",
                        "uri": video_url
                    }
                }
            ]
        }
    }

    return FlexSendMessage(alt_text=title, contents=flex_content)
