import os
import requests
import g4f

from utils.yandex_auth import get_iam_token_from_json_key


class AnalogueFinder:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def find(self, text: str) -> dict:
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

        # --- Единый prompt ---
        prompt = (
            "На основе следующего описания идеи, предложи аналоги: стартапы, сервисы или продукты, "
            "которые реализуют похожую концепцию. Укажи названия и поясни кратко, в чём сходство.\n\n"
            f"Описание:\n{text}"
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

        # # --- Модели g4f ---
        g4f_models = [
            "gpt-4o-mini", "llama-2-7b",
            "gemini-2.0", "blackboxai", "command-r", "qwen-2.5",
            "grok-3-mini", "sonar-pro"
        ]

        for model_name in g4f_models:
            try:
                print(f"⏳ [{model_name}] start...")
                chat_response = g4f.ChatCompletion.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )
                print(f"✅ [{model_name}] done.")
                result[model_name] = chat_response
            except Exception as e:
                result[model_name] = f"Ошибка {model_name}: {str(e)}"
        #
        return result

