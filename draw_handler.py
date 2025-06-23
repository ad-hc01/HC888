# -*- coding: utf-8 -*-
# 本模組專門處理運勢占卜、塔羅牌抽牌與 GPT 解牌，支援今日運勢與三張牌陣（過去／現在／未來）

import random
from openai import OpenAI

client = OpenAI()

def draw_fortune(style: str = "正式風") -> str:
    """
    隨機產生並回傳今日運勢。
    :param style: 回答語氣風格
    """
    fortunes = ["大吉", "中吉", "小吉", "末吉", "凶"]
    result = random.choice(fortunes)
    return f"🧧 今日運勢（{style}）：{result}"

TAROT_CARDS = [
    "愚者", "魔術師", "女祭司", "皇后", "皇帝", "教皇", "戀人", "戰車",
    "力量", "隱者", "命運之輪", "正義", "吊人", "死神", "節制", "惡魔",
    "高塔", "星星", "月亮", "太陽", "審判", "世界"
]

POSITIONS = ["正位", "逆位"]

def draw_tarot_three_cards() -> list[tuple[str, str]]:
    """
    抽出三張塔羅牌，對應過去、現在、未來，並包含正逆位。
    回傳格式為 list[tuple(str, str)]，例如 [("愚者", "正位"), ...]
    """
    drawn = random.sample(TAROT_CARDS, 3)
    result = [(card, random.choice(POSITIONS)) for card in drawn]
    return result

def interpret_tarot_gpt(cards: list[tuple[str, str]], user_question: str = "", style: str = "正式風") -> str:
    """
    使用 GPT 解讀三張塔羅牌含義。
    :param cards: list of (card name, position)
    :param user_question: 使用者問題（選填）
    :param style: 回答語氣風格（正式風／可愛風／幽默風等）
    """
    formatted = "\n".join([
        f"【過去】：{cards[0][0]}（{cards[0][1]}）",
        f"【現在】：{cards[1][0]}（{cards[1][1]}）",
        f"【未來】：{cards[2][0]}（{cards[2][1]}）"
    ])

    prompt = f"""
你是一位專業塔羅牌占卜師，請根據以下三張塔羅牌，分析使用者目前的處境與未來趨勢。

{formatted}
{f'使用者問題：{user_question}' if user_question else ''}
請以「{style}」的語氣回答。
""".strip()

    try:
        chat = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是專業塔羅牌解讀師。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return f"🔮 塔羅占卜結果如下：\n{formatted}\n\n" + chat.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ 無法取得塔羅解讀結果：{e}"

def draw_tarot(user_question: str = "", style: str = "正式風") -> str:
    """
    抽取三張塔羅牌並使用 GPT 解讀結果。
    :param user_question: 使用者問題
    :param style: 回答語氣風格
    """
    cards = draw_tarot_three_cards()
    return interpret_tarot_gpt(cards, user_question, style)
