# -*- coding: utf-8 -*-
# 本檔案負責將圖片套用指定風格，利用 DALL·E 3 生成圖像風格轉換結果
# ✅ 擴充支援 AI 建議風格機制

from openai import OpenAI, OpenAIError

# 初始化 OpenAI 客戶端（自動讀取環境變數 OPENAI_API_KEY）
client = OpenAI()

def suggest_style_prompt(image_url: str) -> str:
    """
    利用 GPT-4o 針對圖片內容推薦合適的風格提示語（供轉風格使用）
    """
    try:
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是圖像風格分析師，請根據圖片內容建議一個適合的藝術風格（例如賽博龐克、水彩畫、油畫、卡漫、未來感、像素風等）。"},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            temperature=0.5,
            max_tokens=100
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        print(f"[suggest_style_prompt] GPT 建議失敗：{e}")
        return "數位插畫"

def generate_stylized_image(image_url: str, style: str | None = None) -> str | None:
    """
    使用 DALL·E 3 以指定風格重新生成圖片，若無風格則由 AI 建議。
    :param image_url: 原始圖片 URL
    :param style: 風格描述，可為 None
    :return: 生成後圖片 URL，失敗則回傳 None
    """
    try:
        if not style:
            style = suggest_style_prompt(image_url)

        prompt = f"將下列圖片以「{style}」風格重新繪製，保持主要內容辨識度。\n圖片 URL：{image_url}"

        resp = client.images.edit(
            model="dall-e-3",
            image={"url": image_url},
            prompt=prompt,
            size="1024x1024",
            response_format="url"
        )
        return resp.data[0].url

    except OpenAIError as e:
        print(f"[generate_stylized_image] OpenAI API error: {e}")
    except Exception as e:
        print(f"[generate_stylized_image] Unexpected error: {e}")
    return None
