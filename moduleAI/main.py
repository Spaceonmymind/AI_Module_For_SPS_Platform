import os
import torch
from models.input import IdeaInput
from parser.text_parser import TextParser
from validator.structure_validator import StructureValidator
from detector.ai_detector import AIDetector
from relevance.freshness_checker import FreshnessChecker
from similarity.analogue_finder import AnalogueFinder
from evaluator.quality_evaluator import QualityEvaluator
from aggregator.result_builder import ResultBuilder
from detector.local import LocalAIDetector


# === Настройка окружения для macOS M1 ===
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
if torch.backends.mps.is_available():
    print("⚙️  MPS найден, но для стабильности используется CPU.")
torch.device("cpu")


class TextAnalysisPipeline:
    def __init__(self):
        print("🧩 Инициализация модулей анализа...\n")
        self.parser = TextParser()
        self.validator = StructureValidator()
        self.detector = AIDetector()
        self.freshness = FreshnessChecker()
        self.similarity = AnalogueFinder()
        self.evaluator = QualityEvaluator()
        self.aggregator = ResultBuilder()
        self.local_detector = LocalAIDetector()
        print("✅ Все компоненты инициализированы.\n")

    def run(self, idea: IdeaInput):
        print("🚀 Запуск анализа текста...")
        try:
            # 1. Парсинг
            print("1️⃣ parser.parse — извлечение разделов...")
            sections = self.parser.parse(idea.text)
            print("  ✓ Разделы извлечены")

            # 2. Проверка структуры
            print("2️⃣ validator.validate — проверка структуры...")
            structure_report = self.validator.validate(sections)
            print("  ✓ Структура проверена")

            # 3. Детекция ИИ
            print("3️⃣ detector.detect — проверка на ИИ (YandexGPT)...")
            ai_detection = self.detector.detect(idea.text)
            print("  ✓ Детекция ИИ завершена")

            # 4. Проверка актуальности
            print("4️⃣ freshness.check — проверка актуальности...")
            outdated_fragments = self.freshness.check(idea.text)
            print("  ✓ Проверка актуальности завершена")

            # 5. Поиск аналогов
            print("5️⃣ similarity.find — поиск аналогов...")
            similar_ideas = self.similarity.find(idea.text)
            print("  ✓ Аналоги найдены")

            # 6. Оценка качества
            print("6️⃣ evaluator.evaluate — оценка качества...")
            quality_scores = self.evaluator.evaluate(idea.text)
            print("  ✓ Оценка качества завершена")

            # 7. Локальный детектор
            print("7️⃣ local_detector.detect — локальный детектор (DistilBERT)...")
            local_analysis = self.local_detector.detect(idea.text)
            print("  ✓ Локальный детектор завершён")

            # 8. Агрегация результатов
            print("8️⃣ aggregator.build — формирование итогового отчёта...")
            final_result = self.aggregator.build(
                structure_report=structure_report,
                ai_detection=ai_detection,
                outdated_fragments=outdated_fragments,
                similar_ideas=similar_ideas,
                quality_scores=quality_scores,
                local_analysis=local_analysis
            )

            print("✅ Анализ успешно завершён!\n")
            return final_result

        except Exception as e:
            print(f"❌ Ошибка во время анализа: {e}")
            raise
