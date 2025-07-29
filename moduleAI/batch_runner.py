import os
from pathlib import Path
from dotenv import load_dotenv
from models.input import IdeaInput
from utils.text_tools import extract_text_from_docx
from main import TextAnalysisPipeline
from pprint import pprint


# Загрузка токенов
load_dotenv()

# Папка с документами
INPUT_FOLDER = Path("data")
OUTPUT_FOLDER = Path("results")
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Запуск
if __name__ == "__main__":
    pipeline = TextAnalysisPipeline()

    docx_files = list(INPUT_FOLDER.glob("*.docx"))
    print(f"Найдено {len(docx_files)} документов\n")

    for idx, filepath in enumerate(docx_files, 1):
        print(f"[{idx}] Обрабатываю: {filepath.name}")
        try:
            text = extract_text_from_docx(filepath)
            input_data = IdeaInput(user_id=idx, text=text)
            result = pipeline.run(input_data)

            output_path = OUTPUT_FOLDER / f"{filepath.stem}_result.json"
            with open(output_path, "w", encoding="utf-8") as f:
                import json
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"  ✔ Сохранено: {output_path.name}\n")

        except Exception as e:
            print(f"  ❌ Ошибка: {e}\n")
