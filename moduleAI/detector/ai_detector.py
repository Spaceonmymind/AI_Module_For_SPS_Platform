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
            "llama-2-7b",
            "gemini-2.0", "blackboxai", "command-r", "qwen-2.5",
            "grok-3-mini", "sonar-pro"
        ]

        for model in g4f_models:
            try:
                print(f"⏳ [{model}] start...")
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": (
                            "Проанализируй текст и определи, был ли он сгенерирован искусственным интеллектом "
                            "или написан человек ом. Объясни, по каким признакам ты сделал вывод. "
                            "Не пиши ничего лишнего, только аналитический вывод.\n\n"
                            f"Текст:\n{text}"
                        )
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
            "llama-2-7b",
            "gemini-2.0", "blackboxai", "command-r", "qwen-2.5",
            "grok-3-mini", "sonar-pro"
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
