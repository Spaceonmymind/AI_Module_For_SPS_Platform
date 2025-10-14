import os
import requests
import g4f

from utils.yandex_auth import get_iam_token_from_json_key


class AnalogueFinder:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        print(f"🔑 AnalogueFinder инициализирован. "
              f"folder_id={self.folder_id}, token={'есть' if self.iam_token else 'нет'}")

    def find(self, text: str) -> dict:
        result = {
            "yandex": None,
            "gemini-2.0": None,
            "command-r": None,
            "gemini-2.0-flash-thinking": None
        }

        # --- Единый prompt ---
        prompt = (
            "На основе следующего описания идеи, предложи аналоги: стартапы, сервисы или продукты, "
            "которые реализуют похожую концепцию. Будь экспертом в области финтеха, ИТ и цифровых сервисов.\n\n"
            "Требования к ответу:\n"
            "1. Для каждой идеи подбери 3–5 аналогов (существующих стартапов, сервисов или продуктов).\n"
            "2. Укажи название аналога (обязательно).\n"
            "3. Опиши кратко, в чём заключается сходство с анализируемой идеей.\n"
            "4. Если есть различия, которые делают аналог менее подходящим, также отметь это.\n\n"
            "Формат ответа:\n"
            "- Аналог: <название>\n"
            "- Сходство: <краткое объяснение>\n"
            "- Отличие: <если есть>\n\n"
            f"Описание идеи:\n{text}"
        )

        # --- Yandex GPT ---
        if self.iam_token and self.folder_id:
            body = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 800
                },
                "messages": [
                    {"role": "system", "text": "Ты эксперт по анализу стартапов и поиску аналогов."},
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
                result["yandex"] = response.json()["result"]["alternatives"][0]["message"]["text"]
            except Exception as e:
                result["yandex"] = f"Ошибка YandexGPT: {str(e)}"
        else:
            result["yandex"] = "YANDEX токен или folder_id не указаны"

        # --- Модели g4f ---
        g4f_models = [
            "gemini-2.0", "command-r",
            "gemini-2.0-flash-thinking"
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

        return result
