import os
import re
import requests
import g4f

from utils.yandex_auth import get_iam_token_from_json_key


class QualityEvaluator:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        print(f"🔑 QualityEvaluator инициализирован. "
              f"folder_id={self.folder_id}, token={'есть' if self.iam_token else 'нет'}")

    def evaluate(self, text: str) -> dict:
        result = {
            "yandex": {},
            "gemini-2.0": {},
            "command-r": {},
            "gemini-2.0-flash-thinking": {}
        }

        # --- Prompt общий для всех моделей ---
        prompt = (
            "Ты — эксперт по финтеху и платёжным системам, оценивающий студенческие идеи. "
            "Оцени строго, как на защите проекта. Средний балл должен быть около 4–5, "
            "а 9–10 ставь только за выдающиеся идеи, которые реально можно внедрить в экосистему платёжных сервисов.\n\n"

            "Критерии оценки:\n"

            "1. Ясность (Clarity):\n"
            "- 1–2: Текст неструктурирован, бессмысленные или противоречивые фразы.\n"
            "- 3–4: Основная мысль угадывается, но плохо изложена.\n"
            "- 5–6: Общая логика есть, но без структуры и конкретики.\n"
            "- 7–8: Хорошая структура, читаемо, но местами размыто.\n"
            "- 9–10: Абсолютно ясно, лаконично, логично, примеры и аргументы выверены.\n\n"

            "2. Выгода (Benefit):\n"
            "- 1–2: Нет никакой реальной пользы, либо идея бессмысленна для пользователей.\n"
            "- 3–4: Польза формальная или надуманная.\n"
            "- 5–6: Есть потенциальная польза, но без доказательств.\n"
            "- 7–8: Явная польза, частично описан эффект.\n"
            "- 9–10: Существенная выгода, просчитанная экономическая или социальная ценность.\n\n"

            "3. Масштабируемость (Scalability):\n"
            "- 1–2: Не масштабируется вообще, привязано к одному контексту.\n"
            "- 3–4: Масштабирование теоретически возможно, но не проработано.\n"
            "- 5–6: Можно расширить с большими трудностями.\n"
            "- 7–8: Масштабируемо при правильной доработке.\n"
            "- 9–10: Изначально рассчитано на рост, масштабируется естественно.\n\n"

            "4. Удобство (Usability):\n"
            "- 1–2: Невозможно понять, как использовать.\n"
            "- 3–4: Описано неочевидно, UX отсутствует.\n"
            "- 5–6: Идея понятна, но реализация вызывает сложности.\n"
            "- 7–8: Удобно и логично, но можно упростить.\n"
            "- 9–10: Максимально интуитивно, простой и понятный пользовательский путь.\n\n"

            "⚠️ Требования к оценке:\n"
            "- Не завышай баллы.\n"
            "- Если идея слабо сформулирована, все критерии ≤3.\n"
            "- Если нет конкретики — снижай оценку до минимума.\n"
            "- Если проект выглядит как шаблонная пустышка без анализа — ставь 1–2.\n"
            "- Используй всю шкалу от 1 до 10.\n\n"

            "Формат ответа (только числа):\n"
            "Ясность: x\n"
            "Выгода: x\n"
            "Масштабируемость: x\n"
            "Удобство: x\n\n"

            f"Анализируемый текст:\n{text}"
        )

        # --- Yandex GPT ---
        if self.iam_token and self.folder_id:
            body = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 600
                },
                "messages": [
                    {"role": "system", "text": "Ты эксперт по оценке стартапов и проектов."},
                    {"role": "user", "text": prompt}
                ]
            }

            try:
                print("📤 [Yandex] Запрос:", body)  # DEBUG
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.iam_token}",
                        "Content-Type": "application/json"
                    },
                    json=body
                )
                print("📥 [Yandex] Статус:", response.status_code)
                print("📥 [Yandex] Ответ (обрезан):", response.text[:300])

                response.raise_for_status()
                content = response.json()["result"]["alternatives"][0]["message"]["text"]
                result["yandex"] = self._parse_scores(content)
            except Exception as e:
                result["yandex"] = {"error": str(e)}
        else:
            result["yandex"] = {"error": "YANDEX токен или folder_id не указаны"}

        # --- Модели G4F --- (все по одной логике)
        g4f_models = [
            "gemini-2.0", "command-r",
            "gemini-2.0-flash-thinking"
        ]

        for model_name in g4f_models:
            try:
                print(f"⏳ [{model_name}] start...")
                response = g4f.ChatCompletion.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )
                print(f"✅ [{model_name}] done.")
                result[model_name] = self._parse_scores(response)
            except Exception as e:
                result[model_name] = {"error": str(e)}

        return result

    def _parse_scores(self, text: str) -> dict:

        mapping = {
            "ясность": ["ясность", "clarity"],
            "выгода": ["выгода", "benefit"],
            "масштабируемость": ["масштабируемость", "scalability"],
            "удобство": ["удобство", "usability", "convenience"]
        }

        scores = {}
        for key, variants in mapping.items():
            for variant in variants:
                match = re.search(rf"{variant}\s*[:\-–]?\s*(\d+)", text, re.IGNORECASE)
                if match:
                    scores[key] = int(match.group(1))
                    break
        return scores
