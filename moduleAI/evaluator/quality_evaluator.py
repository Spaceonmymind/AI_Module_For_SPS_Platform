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

    def evaluate(self, text: str) -> dict:
        result = {
            "yandex": {},
            "gpt-4o-mini": {},
            "llama-2-7b": {},
            "gemini-2.0": {},
            "blackboxai": {},
            "command-r": {},
            "qwen-2.5": {},
            "grok-3-mini": {},
            "sonar-pro": {}
        }

        # --- Prompt общий для всех моделей ---
        prompt = (
            "Оцени идею по 4 критериям от 1 до 10:\n"
            "1. Ясность\n2. Выгода\n3. Масштабируемость\n4. Удобство\n"
            "Формат:\nЯсность: x\nВыгода: x\nМасштабируемость: x\nУдобство: x\n\n"
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

    #     # --- Модели G4F --- (все по одной логике)
        g4f_models = [
            "gpt-4o-mini", "llama-2-7b",
            "gemini-2.0", "blackboxai", "command-r", "qwen-2.5",
            "grok-3-mini", "sonar-pro"
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
    #
        return result
    #
    def _parse_scores(self, text: str) -> dict:
        scores = {}
        for key in ["Ясность", "Выгода", "Масштабируемость", "Удобство"]:
            match = re.search(rf"{key}\s*[:\-–]?\s*(\d+)", text, re.IGNORECASE)
            if match:
                scores[key.lower()] = int(match.group(1))
                return scores
