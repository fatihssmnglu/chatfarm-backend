# knowledge/llm_service.py

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_llm_answer(prompt: str, rag_coverage_ok: bool = True) -> str:
    if not rag_coverage_ok:
        return "Bu konuda yeterli veri yok."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sen bir tarım karar destek uzmanısın."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content