from .gptzero import GPTZeroDetector
from .yandex import YandexGPTDetector
from .local import LocalAIDetector
from .gpt4o import detect_with_gpt
import g4f


class AIDetector:
    def __init__(self):
        self.gptzero = GPTZeroDetector()
        self.yandex = YandexGPTDetector()
        self.local = LocalAIDetector()

    def detect(self, text: str) -> dict:
        results = {
            "gptzero": self.gptzero.detect(text),
            "yandex": self.yandex.detect(text),
            "chatgpt": detect_with_gpt(text)
        }

        # --- Local ---
        local_raw = self.local.detect(text)
        results["local"] = {
            "average_ai_probability": local_raw.get("final_ai_score", 0),
            "likely_generated_snippets": [],
            "repetition_score": 0.0,
            "conclusion": (
                "Текст скорее всего сгенерирован ИИ."
                if local_raw.get("ai_prediction", 0) else "Текст скорее всего написан человеком."
            ),
            "classifiers": local_raw
        }

        # --- g4f модели ---
        g4f_models = [
            "deepseek-v3-0324-turbo",
            "gemini-2.0", "gpt-oss-120b", "command-r", "llama-4-maverick",
            "mistral-small-3.1-24b", "gemini-2.0-flash-thinking"
        ]

        for model in g4f_models:
            try:
                print(f"⏳ [{model}] start...")
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": f"""
                    Определи, написан ли текст человеком или сгенерирован искусственным интеллектом. Проанализируй строго и аргументированно, без лишних вступлений.

                    Важно: текст мог быть написан человеком ПО СТРОГОМУ ШАБЛОНУ (повторяющиеся вопросы/разделы, одинаковая структура карточек). Сам факт шаблонности, однотипных заголовков и последовательности НЕ является признаком ИИ сам по себе — не учитывай это как доказательство ИИ-генерации без других индикаторов.

                    Используй критерии:
                    1) Структура — последовательность, логика; отличай полезную структурированность от «механической шаблонности».
                    2) Стиль и язык — нейтральность/повторяемость/клише vs живая речь, личные обороты.
                    3) Креативность — оригинальные идеи, личные примеры, неожиданные детали.
                    4) Детализация — конкретика и привязка к реальности vs общие фразы.
                    5) Ошибки и шероховатости — естественные оговорки/опечатки/неровности (человек) vs чрезмерная гладкость и однотипность (ИИ).

                    Формат ответа (строго придерживайся):
                    - Структура: <1–2 коротких аргумента>
                    - Стиль и язык: <...>
                    - Креативность: <...>
                    - Детализация: <...>
                    - Ошибки и шероховатости: <...>
                    - Вердикт: текст скорее всего написан человеком | текст скорее всего сгенерирован ИИ
                    - Уверенность: <число от 0 до 100>

                    Текст для анализа:
                    {text}
                    """
                    }],
                    stream=False
                )
                print(f"✅ [{model}] done.")
                results[model] = response
            except Exception as e:
                results[model] = f"Ошибка {model}: {str(e)}"

        # --- Вердикт ---
        verdict = self._aggregate_verdict(results)

        return {
            "sources": results,
            "verdict": verdict
        }

    def _aggregate_verdict(self, results: dict) -> str:
        ai_signals = 0

        local_prob = results.get("local", {}).get("average_ai_probability", 0)
        gptzero_prob = self._extract_percentage(results.get("gptzero", "0%"))
        yandex_text = results.get("yandex", "").lower()
        chatgpt_text = results.get("chatgpt", "").lower()

        if local_prob >= 0.75:
            ai_signals += 1
        if gptzero_prob >= 70:
            ai_signals += 1
        if "сгенерирован" in yandex_text or "нейросеть" in yandex_text:
            ai_signals += 1
        if "сгенерирован" in chatgpt_text or "искусственным интеллектом" in chatgpt_text:
            ai_signals += 1

        for model in [
            "deepseek-v3-0324-turbo",
            "gemini-2.0", "gpt-oss-120b", "command-r", "llama-4-maverick",
            "mistral-small-3.1-24b", "gemini-2.0-flash-thinking"
        ]:
            response = results.get(model)
            if isinstance(response, str):
                text = response.lower()
                if "сгенерирован" in text or "искусственным интеллектом" in text:
                    ai_signals += 1

        if ai_signals >= 5:
            return "Высокая вероятность, что текст сгенерирован ИИ."
        elif ai_signals >= 3:
            return "Возможно, текст содержит ИИ-сгенерированные фрагменты."
        else:
            return "Текст скорее всего написан человеком."

    def _extract_percentage(self, gptzero_output: str) -> float:
        try:
            return float(gptzero_output.replace("%", "").split()[0])
        except:
            return 0.0
