import pandas as pd
import os
from pathlib import Path

# === Настройки ===
excel_path = "/Users/egorgladkih/PycharmProjects/AI_Module_For_SPS_Platform/moduleAI/exported_summary.xlsx"
files_dir = Path("/Users/egorgladkih/PycharmProjects/AI_Module_For_SPS_Platform/moduleAI/data")

# === Чтение Excel ===
df = pd.read_excel(excel_path)
df = df.rename(columns=lambda x: x.strip())

# определяем столбцы автоматически
score_col = [c for c in df.columns if "Score" in c or "оцен" in c][0]
file_col = [c for c in df.columns if "Файл" in c or "file" in c][0]

# === Расчёт приоритетности ===
def priority_level(score):
    if pd.isna(score):
        return "Не определён"
    elif score < 4:
        return "Низкий"
    elif score < 7:
        return "Средний"
    else:
        return "Высокий"

df["Priority"] = df[score_col].apply(priority_level)

# === Сортировка по убыванию оценки ===
df = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)

# === Переименование файлов ===
for i, row in df.iterrows():
    raw_name = str(row[file_col]).strip()
    avg_score = row[score_col]
    priority = row["Priority"]

    # Убираем хвост "_result.json"
    clean_name = raw_name.replace("_result.json", "")
    if not clean_name.endswith(".docx"):
        clean_name += ".docx"

    # Путь старого и нового файла
    old_path = files_dir / clean_name
    new_name = f"{i+1:03d}_{priority}_{avg_score:.2f}_{clean_name}"
    new_path = files_dir / new_name

    if old_path.exists():
        os.rename(old_path, new_path)
        print(f"✅ {clean_name} → {new_name}")
    else:
        print(f"⚠️ Не найден: {clean_name}")

# === Финальная сводка ===
print("\n🎯 Готово! Все DOCX переименованы по убыванию оценки.")
print(df[[file_col, score_col, "Priority"]].head(10))
