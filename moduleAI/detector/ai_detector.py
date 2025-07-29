from .gptzero import GPTZeroDetector
from .yandex import YandexGPTDetector
from .local import LocalAIDetector
from .chatgpt import detect_with_gpt

class AIDetector:
    """
    Универсальный детектор: агрегирует все методы — GPTZero, YandexGPT, Local BERT.
    """

    def __init__(self):
        self.gptzero = GPTZeroDetector()
        self.yandex = YandexGPTDetector()
        self.local = LocalAIDetector()


    def detect(self, text: str) -> dict:
        chatgpt_result = detect_with_gpt(text)
        results = {
            "gptzero": self.gptzero.detect(text),
            "yandex": self.yandex.detect(text),
            "chatgpt": chatgpt_result,
            "local": self.local.detect(text)
        }

        # Генерация итогового вердикта
        verdict = self._aggregate_verdict(results)

        return {
            "sources": results,
            "verdict": verdict
        }

    def _aggregate_verdict(self, results: dict) -> str:
        local_prob = results["local"]["average_ai_probability"]
        gptzero_prob = self._extract_percentage(results["gptzero"])
        yandex_text = results["yandex"].lower()
        chatgpt_text = results["chatgpt"].lower()

        ai_signals = 0

        if local_prob >= 0.75:
            ai_signals += 1
        if gptzero_prob >= 70:
            ai_signals += 1
        if "сгенерирован" in yandex_text or "нейросеть" in yandex_text:
            ai_signals += 1
        if "сгенерирован" in chatgpt_text or "искусственным интеллектом" in chatgpt_text:
            ai_signals += 1

        if ai_signals == 3:
            return "Высокая вероятность, что текст сгенерирован ИИ."
        elif ai_signals == 2:
            return "Возможно, текст содержит ИИ-сгенерированные фрагменты."
        else:
            return "Текст скорее всего написан человеком."

    def _extract_percentage(self, gptzero_output: str) -> float:
        try:
            return float(gptzero_output.replace("%", "").split()[0])
        except:
            return 0.0
