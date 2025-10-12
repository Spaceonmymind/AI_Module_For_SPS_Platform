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
            "gpt-4o-mini": {},
            "deepseek-v3-0324-turbo": {},
            "gemini-2.0": {},
            "gpt-oss-120b": {},
            "command-r": {},
            "llama-4-maverick": {},
            "mistral-small-3.1-24b": {},
            "gemini-2.0-flash-thinking": {}
        }

        # --- Prompt общий для всех моделей ---
        prompt = (
            "Оцени идею по 4 критериям от 1 до 10. "
            "Будь строгим, представь, что ты эксперт в платёжных технологиях, "
            "который проверяет артефакты на курсе сервисов платёжных систем.\n\n"

            "Критерии оценки:\n"
            "1. Ясность (Clarity):\n"
            "- 1–3: Текст запутанный, вода, непонятные термины.\n"
            "- 4–6: Идея в целом понятна, но формулировки размытые или дублируются.\n"
            "- 7–8: Чётко и логично, но есть избыточность или пробелы.\n"
            "- 9–10: Максимальная ясность, структурированность, конкретные примеры.\n\n"

            "2. Выгода (Benefit):\n"
            "- 1–3: Нет пользы для пользователя или рынка.\n"
            "- 4–6: Польза есть, но описана общо, эффект сомнителен.\n"
            "- 7–8: Ценность для аудитории есть, но мало расчётов.\n"
            "- 9–10: Явная и значимая выгода, чёткий экономический/социальный эффект.\n\n"

            "3. Масштабируемость (Scalability):\n"
            "- 1–3: Решение локальное, не масштабируется.\n"
            "- 4–6: Есть потенциал, но есть серьёзные барьеры.\n"
            "- 7–8: Масштабируемо, но требует доработок и ресурсов.\n"
            "- 9–10: Легко масштабируется, архитектура рассчитана на рост.\n\n"

            "4. Удобство (Usability):\n"
            "- 1–3: Сложно для восприятия или использования.\n"
            "- 4–6: Используемо, но процесс неочевиден.\n"
            "- 7–8: Удобно, понятный UX, но есть мелкие барьеры.\n"
            "- 9–10: Максимальная простота и удобство, минимум действий.\n\n"

            "Формат ответа:\n"
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
            "deepseek-v3-0324-turbo", "gpt-4o-mini",
            "gemini-2.0", "gpt-oss-120b", "command-r", "llama-4-maverick",
            "mistral-small-3.1-24b", "gemini-2.0-flash-thinking"
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
