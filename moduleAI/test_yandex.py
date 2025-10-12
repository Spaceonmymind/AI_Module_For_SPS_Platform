import os
import requests
from utils.yandex_auth import get_iam_token_from_json_key

API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def test_yandex_gpt():
    iam_token = get_iam_token_from_json_key()
    folder_id = os.getenv("YANDEX_FOLDER_ID")

    if not iam_token or not folder_id:
        print("❌ Нет IAM токена или YANDEX_FOLDER_ID")
        return

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json"
    }

    body = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 200
        },
        "messages": [
            {"role": "system", "text": "Ты умный помощник."},
            {"role": "user", "text": "Привет, напиши короткий тост про IT на 2 предложения."}
        ]
    }

    print("📤 Отправляю запрос:", body)
    response = requests.post(API_URL, headers=headers, json=body)
    print("📥 Статус:", response.status_code)
    print("📥 Ответ RAW:", response.text[:500])  # первые 500 символов

    if response.ok:
        result = response.json()
        text = result["result"]["alternatives"][0]["message"]["text"]
        print("✅ Ответ Yandex GPT:", text)

if __name__ == "__main__":
    test_yandex_gpt()
