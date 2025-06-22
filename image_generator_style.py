# -*- coding: utf-8 -*-
# 本檔案負責將圖片套用指定風格，利用 GPT-4o 生成圖像風格轉換結果

import openai

def generate_stylized_image(image_url: str, style: str) -> str:
    """
    使用 GPT-4o 將圖片轉換成指定風格，回傳圖像 URL
    """
    try:
        response = openai.images.edit(
            model="dall-e-3",
            image={"url": image_url},
            prompt=f"以 {style} 風格重新生成這張圖片",
            size="1024x1024",
            response_format="url"
        )
        return response.data[0].url
    except Exception as e:
        print(f"[Stylized Image Error] {e}")
        return None
