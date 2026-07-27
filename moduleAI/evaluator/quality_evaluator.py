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

        print(f"🔑 QualityEvaluator инициализирован. "
              f"folder_id={self.folder_id}, token={'есть' if self.iam_token else 'нет'}")

    def evaluate(self, text: str) -> dict:
        result = {
            "yandex": {},
            "gemini-2.0": {},
            "command-r": {},
            "gemini-2.0-flash-thinking": {}
        }

        # --- Prompt общий для всех моделей ---
        prompt = (
            "Ты — эксперт по финтеху, цифровым платформам и архитектуре платёжных сервисов, "
            "а также по анализу проектной и технической документации. "
            "Перед тобой один документ — «Аннотация реализации сервиса», подготовленный одним участником.\n\n"

            "🎯 ТВОЯ ЗАДАЧА:\n"
            "- Оценить аннотацию по 5 критериям (1–10);\n"
            "- Оценивать ТОЛЬКО содержательную и логическую часть документа;\n"
            "- НЕ учитывать оформление, шрифты, стили Word, ГОСТ и формальные требования;\n"
            "- НЕ учитывать объём текста, количество страниц, таблиц или рисунков;\n"
            "- НЕ оценивать грамотность, академичность или красивость формулировок.\n\n"

            "🔍 ФОКУС ВНИМАНИЯ — ТОЛЬКО СОДЕРЖАНИЕ ОБОСНОВАНИЯ:\n"
            "- Насколько ясно сформулирована идея сервиса и решаемая проблема;\n"
            "- Есть ли акторы и корректно ли описаны их роли и функции;\n"
            "- Есть ли логика процессов AS IS и TO BE и понятно ли, что именно меняется;\n"
            "- Есть ли архитектурное мышление (компоненты, модули, взаимодействия);\n"
            "- Понятно ли, КАК сервис работает технически;\n"
            "- Насколько решение реалистично в контексте финтех-инфраструктуры (API, банки, платёжные системы).\n\n"

            "❗ ВАЖНО: объём текста НЕ должен повышать оценку.\n"
            "- Большое количество страниц или схем НЕ увеличивают баллы.\n"
            "- Большой текст ≠ хорошее обоснование.\n"
            "- Короткое, но логичное и технически корректное обоснование может получить высокую оценку.\n"
            "- Длинный документ без архитектуры, акторов и процессов должен получить низкую оценку.\n\n"

            "📘 Аннотация должна содержать (но оцени только по сути, не по формальной структуре):\n"
            "1. Введение;\n"
            "2. Анализ аналогов;\n"
            "3. Архитектура сервиса;\n"
            "4. Области применения сервиса;\n"
            "5. Экономическую эффективность.\n"
            "6. Заключение\n"

            "📊 КРИТЕРИИ ОЦЕНКИ (1–10):\n\n"

            "1. Ясность идеи и логики:\n"
            "- Насколько понятна идея сервиса и логика её работы.\n\n"

            "2. Проработка акторов и ролей:\n"
            "- Корректность выделения акторов и их функций.\n\n"

            "3. Архитектура и внутренняя логика сервиса:\n"
            "- Наличие компонентов, модулей и логики взаимодействий.\n\n"

            "4. Реализуемость и обоснованность:\n"
            "- Реалистичность решения в рамках финтех-инфраструктуры.\n\n"

            "⚠️ ПРАВИЛА ЖЁСТКОЙ ОЦЕНКИ:\n"
            "- НЕ оценивай по объёму или оформлению.\n"
            "- Если нет акторов или процессов — максимум 5–6.\n"
            "- Если нет архитектуры или внутренней логики — максимум 4–5.\n"
            "- Если идея противоречит финтех-реальности — максимум 3–4.\n"
            "- Используй всю шкалу от 1 до 10.\n\n"

            "Формат ответа (строго соблюдать):\n"
            "Ясность идеи: x\n"
            "Акторы и роли: x\n"
            "AS IS / TO BE: x\n"
            "Архитектура сервиса: x\n"
            "Реализуемость: x\n\n"
            "Краткий вывод:\n"
            "- 3–5 предложений о сильных сторонах и ключевых проблемах обоснования.\n\n"

            f"Анализируемый текст (обоснование одного участника):\n{text}"
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
                content = response.json()["result"]["alternatives"][0]["message"]["text"]
                result["yandex"] = self._parse_scores(content)
            except Exception as e:
                result["yandex"] = {"error": str(e)}
        else:
            result["yandex"] = {"error": "YANDEX токен или folder_id не указаны"}

        # --- Модели G4F --- (все по одной логике)
        g4f_models = [
            "gemini-2.0", "command-r",
            "gemini-2.0-flash-thinking"
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

        return result

    def _parse_scores(self, text: str) -> dict:
        """
        Парсит оценки для ОБОСНОВАНИЯ (5 критериев).
        Ожидаемый формат:
        Ясность идеи: x
        Акторы и роли: x
        AS IS / TO BE: x
        Архитектура сервиса: x
        Реализуемость: x
        """
        mapping = {
            "clarity": ["ясность идеи", "ясность", "clarity"],
            "actors": ["акторы и роли", "акторы", "actors"],
            "as_is_to_be": ["as is / to be", "as is to be", "as-is/to-be", "as is/to be", "to be", "as is"],
            "architecture": ["архитектура сервиса", "архитектура", "architecture"],
            "feasibility": ["реализуемость", "обоснованность", "feasibility", "viability"]
        }

        scores = {}
        for key, variants in mapping.items():
            for v in variants:
                # ищем: <ключ> : 7  или <ключ> - 7
                m = re.search(rf"{re.escape(v)}\s*[:\-–]?\s*(\d+)", text, re.IGNORECASE)
                if m:
                    scores[key] = int(m.group(1))
                    break

        return {"justification": scores}

        def extract_scores(block: str) -> dict:
            mapping = {
                "ясность": ["ясность", "clarity"],
                "выгода": ["выгода", "benefit"],
                "масштабируемость": ["масштабируемость", "scalability"],
                "архитектура": ["архитектура", "journey", "usability", "architecture"]
            }
            scores = {}
            for key, variants in mapping.items():
                for variant in variants:
                    match = re.search(rf"{variant}\s*[:\-–]?\s*(\d+)", block, re.IGNORECASE)
                    if match:
                        scores[key] = int(match.group(1))
                        break
            return scores

        for idx, block in enumerate(essays, start=1):
            if "средн" in block.lower():
                results["average"] = extract_scores(block)
            else:
                results[f"essay_{idx}"] = extract_scores(block)

        # Если модель не вывела средние — посчитаем их сами
        if "average" not in results and all(f"essay_{i}" in results for i in (1, 2, 3)):
            avg_scores = {}
            keys = ["ясность", "выгода", "масштабируемость", "архитектура"]
            for key in keys:
                values = [results[f"essay_{i}"].get(key, 0) for i in (1, 2, 3)]
                avg = sum(values) / len([v for v in values if v > 0]) if any(values) else 0
                avg_scores[key] = round(avg, 2)
            results["average"] = avg_scores

        return results
