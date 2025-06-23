# -*- coding: utf-8 -*-
# 本模組負責將使用者輸入的風格名稱轉換為對應的繪圖提示（prompt），
# 並進一步用 GPT 強化主題、構圖、風格細節，提升生成圖像品質

from openai import OpenAI

client = OpenAI()

style_map = {
    "哥德風": "gothic, dark shadows, cathedral, gothic horror",
    "賽博龐克": "cyberpunk, neon lights, futuristic, sci-fi city",
    "可愛風": "kawaii, pastel colors, big round eyes, cute characters",
    "寫實風": "ultra realistic, 8K details, natural lighting, lifelike",
    "手繪風": "sketch drawing, pencil line art, hand drawn texture",
    "油畫風": "oil painting, thick brush strokes, canvas texture",
    "水彩風": "watercolor, soft strokes, subtle blending, art paper texture",
    "日系風": "anime style, Japanese art, vibrant colors, clean lines",
    "歐美風": "western comic style, bold outlines, dynamic poses",
    "吉卜力風": "Ghibli style, soft watercolor, nostalgic scenery, whimsical",
    "皮克斯風": "Pixar style, 3D animation, expressive eyes, cinematic lighting",
    "迪士尼風": "Disney style, fairytale, charming, large sparkly eyes",
    "夢工廠風": "DreamWorks style, stylized 3D, humorous, expressive faces",
    "抽象風": "abstract, geometric patterns, vivid colors, non-representational",
    "未來主義": "futurism, metallic textures, high-tech, minimal neon aesthetics",
    "復古風": "retro style, 80s neon lights, analog textures, vintage vibe",
    "暗黑奇幻風": "dark fantasy, cursed forest, mystical creatures, shadow magic",
    "神話風": "mythological, greek gods, ancient temples, divine glow",
    "宮廷風": "baroque, victorian palace, gold patterns, royal dress",
    "武俠風": "wuxia, ancient China, sword fight, misty mountains",
    "中式水墨風": "Chinese ink painting, brush strokes, mountain and river",
    "洛可可風": "rococo, ornate, pastel, romantic elegance",
    "簡約風": "minimalist, clean design, soft tones, empty space"
}

def enhance_prompt_with_style(prompt: str, style: str = "") -> str:
    """
    將風格關鍵字轉為英文繪圖提示，並用 GPT 生成完整圖像描述。
    :param prompt: 主題描述
    :param style: 風格關鍵詞（中文）
    :return: 英文提示詞（可送入 DALL·E）
    """
    style_prompt = ""
    for key, val in style_map.items():
        if key in style:
            style_prompt = val
            break

    try:
        gpt_prompt = f"{prompt}, {style_prompt}" if style_prompt else prompt
        system_msg = (
            "你是專業圖像提示優化師，請將使用者輸入的圖像主題轉為高品質英文提示，"
            "補充場景氛圍、藝術風格、構圖與細節，輸出一行完整英文即可。"
        )

        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": gpt_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        return result.choices[0].message.content.strip()
    except Exception as e:
        print(f"[enhance_prompt_with_style] Error: {e}")
        return prompt + ", digital art"
