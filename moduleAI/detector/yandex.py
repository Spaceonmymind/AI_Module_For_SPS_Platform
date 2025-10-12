import os
import requests
from utils.yandex_auth import get_iam_token_from_json_key


class YandexGPTDetector:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        print(f"🔑 YandexGPTDetector инициализирован. "
              f"folder_id={self.folder_id}, token={'есть' if self.iam_token else 'нет'}")

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
                "temperature": 0.3,
                "maxTokens": 500
            },
            "messages": [
                {"role": "system", "text": "Ты эксперт по выявлению ИИ-сгенерированного текста. Имей в виду, что некоторые тексты написаны людьми по заранее заданному шаблону (например, карточки идей с одинаковыми вопросами и разделами: «КЛИЕНТСКИЕ БОЛИ», «ТАБЛЕТКА ОТ КЛИЕНТСКОЙ БОЛИ» и т.п.). Поэтому структурированность и повторяемость разделов сами по себе не доказывают ИИ-генерацию."},
                {"role": "user", "text": f"Определи, был ли этот текст сгенерирован искусственным интеллектом или написан человеком. Учитывай, что текст может быть по строгому шаблону. Оцени по признакам: 1. Есть ли личные детали, примеры и опыт автора (признак человека). 2. Есть ли нестандартные или противоречивые элементы, ошибки, разговорные выражения (признак человека). 3. Есть ли клишированные формулировки, однообразный стиль, чрезмерная гладкость текста (признак ИИ). 4. Есть ли повторяемость формата ответов без вариативности (признак ИИ). Анализируемый текст:\n{text}"}
            ]
        }

        try:
            print("📤 [Yandex] Запрос:", payload)  # DEBUG
            response = requests.post(self.api_url, headers=headers, json=payload)
            print("📥 [Yandex] Статус:", response.status_code)
            print("📥 [Yandex] Ответ (обрезан):", response.text[:300])

            response.raise_for_status()
            result = response.json()
            content = result["result"]["alternatives"][0]["message"]["text"]
            return content.strip()

        except Exception as e:
            return f"Ошибка YandexGPT: {e}"
