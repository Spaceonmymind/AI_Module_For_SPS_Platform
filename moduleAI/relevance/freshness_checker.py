import os
import requests
import g4f

from utils.yandex_auth import get_iam_token_from_json_key


class FreshnessChecker:
    def __init__(self):
        self.iam_token = get_iam_token_from_json_key()
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        print(f"🔑 FreshnessChecker инициализирован. "
              f"folder_id={self.folder_id}, token={'есть' if self.iam_token else 'нет'}")

    def check(self, text: str) -> dict:
        result = {
            "yandex": None,
            "gpt-4o-mini": None,
            "deepseek-v3-0324-turbo": None,
            "gemini-2.0": None,
            "gpt-oss-120b": None,
            "command-r": None,
            "llama-4-maverick": None,
            "mistral-small-3.1-24b": None,
            "gemini-2.0-flash-thinking": None
        }

        # --- Промпт общий для всех моделей ---
        prompt = (
            "Проанализируй следующий текст и определи, содержит ли он устаревшие технологии, идеи, подходы, термины или примеры. "
            "Будь строгим экспертом в области ИТ, финтеха и цифровых сервисов.\n\n"
            "Требования к анализу:\n"
            "1. Укажи конкретные фрагменты текста, которые выглядят устаревшими или неактуальными.\n"
            "2. Объясни, почему они устарели (например: технологии больше не применяются, есть новые стандарты, терминология изменилась).\n"
            "3. Предложи современные аналоги или подходы для замены (с учётом трендов: AI, блокчейн, open API, cloud-native, UX/UI, цифровые идентификаторы и т.п.).\n\n"
            "Формат ответа:\n"
            "- Устаревший фрагмент: <цитата>\n"
            "- Почему устарел: <объяснение>\n"
            f"Анализируемый текст:\n{text}"
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
                    {"role": "system",
                     "text": "Ты специалист по отслеживанию устаревших идей, терминов и технологий в тексте."},
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

        # --- Модели G4F ---
        g4f_models = [
            "deepseek-v3-0324-turbo", "gpt-4o-mini",
            "gemini-2.0", "gpt-oss-120b", "command-r", "llama-4-maverick",
            "mistral-small-3.1-24b", "gemini-2.0-flash-thinking"
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

        return result
