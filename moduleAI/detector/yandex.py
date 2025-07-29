import os
import requests
from utils.yandex_auth import get_iam_token_from_json_key

class YandexGPTDetector:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def detect(self, text: str) -> str:
        if not self.iam_token or not self.folder_id:
            return "Ошибка YandexGPT: нет токена или folder_id"

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.2,
                "maxTokens": 500
            },
            "messages": [
                {"role": "system", "text": "Ты эксперт по выявлению ИИ-сгенерированного текста."},
                {"role": "user", "text": f"Определи, был ли этот текст сгенерирован ИИ:\n\n{text}"}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()['result']['alternatives'][0]['message']['text']
            return content.strip()
        except Exception as e:
            return f"Ошибка YandexGPT: {e}"
