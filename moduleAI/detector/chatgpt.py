import g4f

def detect_with_gpt(text: str) -> str:
    prompt = (
        "Проанализируй текст и определи, был ли он сгенерирован искусственным интеллектом или написан человеком. "
        "Объясни, по каким признакам ты сделал вывод. Не пиши ничего лишнего, только аналитический вывод.\n\n"
        f"Текст:\n{text}"
    )
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return response
    except Exception as e:
        return f"Ошибка ChatGPT (g4f): {str(e)}"
