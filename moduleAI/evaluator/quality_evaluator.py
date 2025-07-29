import os
import requests
import g4f  # ← добавляем библиотеку

from utils.yandex_auth import get_iam_token_from_json_key


class QualityEvaluator:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def evaluate(self, text: str) -> dict:
        result = {
            "yandex": {},
            "chatgpt": {}
        }

        # --- YandexGPT часть ---
        if self.iam_token and self.folder_id:
            criteria_prompt = (
                "**Оцени идею по 4 критериям от 1 до 10 и дай ей краткое описание:**\n"
                "1. **Ясность** — насколько идея изложена чётко, логично и понятно.\n"
                "2. **Выгода** — какую конкретную пользу приносит идея (экономическую, социальную, временную).\n"
                "3. **Масштабируемость** — может ли идея быть расширена, адаптирована под другие случаи/регионы.\n"
                "4. **Удобство** — насколько легко пользователю воспользоваться идеей на практике.\n\n"
                "Пример формата вывода:\n"
                "Ясность: 8\n"
                "Выгода: 7\n"
                "Масштабируемость: 6\n"
                "Удобство: 9\n\n"
                f"Анализируй следующий текст:\n{text}"
            )

            body = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 600
                },
                "messages": [
                    {"role": "system", "text": "Ты эксперт по оценке стартапов и проектов."},
                    {"role": "user", "text": criteria_prompt}
                ]
            }

            try:
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.iam_token}",
                        "Content-Type": "application/json"
                    },
                    json=body
                )
                response.raise_for_status()
                content = response.json()['result']['alternatives'][0]['message']['text']
                result["yandex"] = self._parse_scores(content)
            except Exception as e:
                result["yandex"] = {"error": str(e)}
        else:
            result["yandex"] = {"error": "YANDEX токен или folder_id не указаны"}

        # --- GPT-4o часть через g4f ---
        try:
            prompt = (
                "Оцени идею по 4 критериям от 1 до 10:\n"
                "1. Ясность\n2. Выгода\n3. Масштабируемость\n4. Удобство\n"
                "Формат:\nЯсность: x\nВыгода: x\nМасштабируемость: x\nУдобство: x\n\n"
                f"Анализируемый текст:\n{text}"
            )

            response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            result["chatgpt"] = self._parse_scores(response)
        except Exception as e:
            result["chatgpt"] = {"error": str(e)}

        return result

    def _parse_scores(self, text: str) -> dict:
        import re

        scores = {}
        for key in ["Ясность", "Выгода", "Масштабируемость", "Удобство"]:
            match = re.search(rf"{key}\s*[:\-–]?\s*(\d+)", text, re.IGNORECASE)
            if match:
                scores[key.lower()] = int(match.group(1))
        return scores
