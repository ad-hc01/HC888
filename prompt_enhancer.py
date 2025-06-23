# -*- coding: utf-8 -*-
# 本模組負責將使用者輸入的風格名稱轉換為對應的繪圖提示，並回傳強化後的 prompt

from typing import Optional


def enhance_prompt_with_style(prompt: str, style: str = "") -> str:
    """
    接收原始 prompt 和可選的風格關鍵字，
    回傳注入風格提示的完整繪圖描述。
    若 style 為空或找不到對應，回傳原 prompt。
    """
    # 風格映射表
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

    matched_style_prompt: Optional[str] = None
    for key, val in style_map.items():
        if key in style:
            matched_style_prompt = val
            break

    if matched_style_prompt:
        enhanced = f"{prompt}, {matched_style_prompt}"
        print(f"[DEBUG] Prompt enhanced with style {style!r}: {enhanced}")
        return enhanced
    else:
        if style:
            print(f"[DEBUG] 未匹配到風格：{style!r}")
        return prompt
