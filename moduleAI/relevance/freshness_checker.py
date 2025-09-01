import os
import requests
import g4f

from utils.yandex_auth import get_iam_token_from_json_key


class FreshnessChecker:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def check(self, text: str) -> dict:
        result = {
            "yandex": None,
            "gpt-4o-mini": None,
            "llama-2-7b": None,
            "gemini-2.0": None,
            "blackboxai": None,
            "command-r": None,
            "qwen-2.5": None,
            "grok-3-mini": None,
            "sonar-pro": None
        }

        # --- Промпт общий для всех моделей ---
        prompt = (
            "Проанализируй следующий текст и определи, содержит ли он устаревшие технологии, идеи, подходы, "
            "термины или примеры. Укажи, какие именно фрагменты неактуальны и чем их можно заменить на современные аналоги.\n\n"
            f"Текст:\n{text}"
        )

        # --- YandexGPT ---
        if self.iam_token and self.folder_id:
            body = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 800
                },
                "messages": [
                    {"role": "system",
                     "text": "Ты специалист по отслеживанию устаревших идей, терминов и технологий в тексте."},
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
                result["yandex"] = response.json()['result']['alternatives'][0]['message']['text']
            except Exception as e:
                result["yandex"] = f"Ошибка YandexGPT: {str(e)}"
        else:
            result["yandex"] = "YANDEX токен или folder_id не указаны"

        # --- Модели G4F ---
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
                result[model_name] = response
            except Exception as e:
                result[model_name] = f"Ошибка {model_name}: {str(e)}"
        #
        return result
        #
