# -*- coding: utf-8 -*-
# 本檔案為抽卡模組，支援運勢抽卡、塔羅牌占卜、自訂卡池抽卡

import random

# 運勢卡池
FORTUNE_LIST = [
    "🌟 大吉：今天萬事順利！適合展開新計畫。",
    "😊 中吉：一切平穩，保持心情愉快。",
    "😐 小吉：有點小挑戰，但你可以應付。",
    "⚠️ 凶：注意情緒與健康，凡事放慢腳步。",
    "💤 平：平淡是福，保持低調。",
]

# 塔羅牌簡單示例
TAROT_LIST = [
    "🌞 太陽（正位）：成功、快樂與滿足。",
    "🌚 月亮（逆位）：迷惘、不安，需多觀察。",
    "👑 皇帝（正位）：掌控權力、秩序井然。",
    "💔 塔（逆位）：警示改變，重建之路。",
    "🌟 星星（正位）：希望、靈感與療癒。",
]

def draw_fortune():
    """抽取今日運勢"""
    return f"🔮 今日運勢：{random.choice(FORTUNE_LIST)}"

def draw_tarot():
    """抽取塔羅牌"""
    return f"🃏 你的塔羅牌是：{random.choice(TAROT_LIST)}"

def draw_custom(pool):
    """從自訂卡池中抽取"""
    if not pool:
        return "❌ 卡池為空，請先設定自訂卡池內容。"
    return f"🎲 你抽到的是：{random.choice(pool)}"
