import os
import requests
import g4f  # ← добавляем поддержку gpt-4o

from utils.yandex_auth import get_iam_token_from_json_key


class FreshnessChecker:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def check(self, text: str) -> dict:
        result = {
            "yandex": None,
            "chatgpt": None
        }

        # --- Проверка через Yandex GPT ---
        if self.iam_token and self.folder_id:
            system_msg = "Ты специалист по отслеживанию устаревших идей, терминов и технологий в тексте."
            prompt = (
                "Проанализируй следующий текст и определи, содержит ли он устаревшие технологии, идеи, подходы, "
                "термины или примеры. Укажи, какие именно фрагменты неактуальны и чем их можно заменить на современные аналоги.\n\n"
                f"Текст:\n{text}"
            )

            body = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 800
                },
                "messages": [
                    {"role": "system", "text": system_msg},
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

        # --- Проверка через GPT-4o (g4f) ---
        try:
            gpt_prompt = (
                "Проведи анализ текста и ответь, содержит ли он устаревшие термины, технологии или примеры. "
                "Если да — перечисли их и предложи актуальные аналоги.\n\n"
                f"Текст:\n{text}"
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
