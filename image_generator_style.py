# -*- coding: utf-8 -*-
# 本檔案負責將圖片套用指定風格，利用 DALL·E 3 生成圖像風格轉換結果，並回傳圖像 URL 或 None

import logging
from openai import OpenAI, OpenAIError

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

def generate_stylized_image(image_url: str, style: str) -> str | None:
    """
    使用 DALL·E 3 以指定風格重新生成圖片，並回傳圖像 URL。
    :param image_url: 原始圖片 URL
    :param style: 風格描述
    :return: 生成後圖片 URL，失敗則回傳 None
    """
    prompt = (
        f"將下列圖片以「{style}」風格重新繪製，保持主要內容辨識度。\n"
        f"圖片 URL：{image_url}"
    )
    logging.debug(f"[generate_stylized_image] called with image_url={image_url!r}, style={style!r}")
    try:
        resp = client.images.edit(
            model="dall-e-3",
            image={"url": image_url},
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        url = resp.data[0].url
        logging.debug(f"[generate_stylized_image] success URL: {url}")
        return url
    except OpenAIError as e:
        logging.error(f"[generate_stylized_image] OpenAIError: {e}")
    except Exception as e:
        logging.error(f"[generate_stylized_image] Unexpected error: {e}")
    return None
