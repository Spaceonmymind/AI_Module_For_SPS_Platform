import os
import requests
import g4f  # подключаем поддержку gpt-4o

from utils.yandex_auth import get_iam_token_from_json_key


class AnalogueFinder:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def find(self, text: str) -> dict:
        result = {
            "yandex": None,
            "chatgpt": None
        }

        # --- Поиск аналогов через Yandex GPT ---
        if self.iam_token and self.folder_id:
            prompt = (
                "Ты аналитик стартапов. На основе представленного описания идеи определи похожие проекты, "
                "сервисы или стартапы в России или за рубежом. Назови конкретные названия и кратко поясни, чем они похожи.\n\n"
                f"Описание:\n{text}"
            )

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

        # --- Поиск аналогов через GPT-4o ---
        try:
            gpt_prompt = (
                "На основе следующего описания идеи, предложи аналоги: стартапы, сервисы или продукты, "
                "которые реализуют похожую концепцию. Укажи названия и поясни кратко, в чём сходство.\n\n"
                f"Описание:\n{text}"
            )

            chat_response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": gpt_prompt}],
                stream=False
            )

            result["chatgpt"] = chat_response
        except Exception as e:
            result["chatgpt"] = f"Ошибка ChatGPT (g4f): {str(e)}"

        return result
