# -*- coding: utf-8 -*-
# 本模組為「梅花易數」功能，模擬時間起卦並由 GPT 分析卦象意涵

import random
from datetime import datetime
from openai import OpenAI

client = OpenAI()
TRIGRAMS = ["☰ 乾", "☱ 兌", "☲ 離", "☳ 震", "☴ 巽", "☵ 坎", "☶ 艮", "☷ 坤"]

def generate_meihua_hexagram() -> str:
    now = datetime.now()
    seed = int(now.strftime("%Y%m%d%H%M%S"))
    random.seed(seed)
    upper = random.randint(0, 7)
    lower = random.randint(0, 7)
    moving_lines = [random.choice([True, False]) for _ in range(6)]

    upper_name = TRIGRAMS[upper]
    lower_name = TRIGRAMS[lower]

    gpt_prompt = f"""
請以簡單親切語氣解釋此梅花易數卦象：
- 上卦：{upper_name}
- 下卦：{lower_name}
- 六爻（自下而上）：{["動" if m else "靜" for m in moving_lines]}
請給出現代人可理解的生活建議。
""".strip()

    try:
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位通曉易經的梅花易數老師，請用生活化的方式回應。"},
                {"role": "user", "content": gpt_prompt}
            ],
            temperature=0.8,
            max_tokens=600
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 無法生成卦象分析：{e}"
