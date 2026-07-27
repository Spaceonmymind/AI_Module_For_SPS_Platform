import os
import json
import pandas as pd

RESULTS_DIR = "/Users/egorgladkih/PycharmProjects/AI_Module_For_SPS_Platform/moduleAI/results"
EXPORT_PATH = "/Users/egorgladkih/PycharmProjects/AI_Module_For_SPS_Platform/moduleAI/exported_summary.xlsx"

def parse_result(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    row = {"Файл": os.path.basename(filepath)}

    # --- Структура эссе ---
    structure = data.get("structure_validation", {})
    row.update({
        "is_essay": structure.get("is_essay", ""),
        "structure_valid": structure.get("valid", ""),
        "structure_message": structure.get("message", ""),
        "missing_sections": ", ".join(structure.get("missing_sections", [])) if isinstance(structure.get("missing_sections"), list) else ""
    })

    # --- AI Detection ---
    detection = data.get("ai_detection", {})
    row["ai_verdict"] = detection.get("verdict", "")
    sources = detection.get("sources", {}) or {}
    for model, verdict in sources.items():
        if isinstance(verdict, dict):
            for k, v in verdict.items():
                row[f"AI Verdict [{model}]: {k}"] = v
        else:
            row[f"AI Verdict [{model}]"] = verdict

    # --- Local Verdict ---
    local = sources.get("local", {}) or {}
    row.update({
        "Local Verdict": local.get("verdict", ""),
        "Local Score": local.get("score", ""),
        "Local Comment": local.get("comment", "")
    })

    # --- Freshness ---
    freshness = data.get("freshness_check", {}) or {}
    for model, answer in freshness.items():
        row[f"Freshness [{model}]"] = answer

    # --- Similar Ideas ---
    similar = data.get("similar_ideas", {}) or {}
    for model, answer in similar.items():
        row[f"Similar Ideas [{model}]"] = answer

    # --- Quality Evaluation ---
    quality = data.get("quality_evaluation", {}) or {}

    # будем хранить наборы оценок по моделям, чтобы выбрать "главный" для Average Score
    model_score_sets = {}  # llm -> list[float]

    def flatten_scores(prefix: str, obj):
        """
        Рекурсивно разворачивает dict с оценками в row,
        возвращает список числовых значений (int/float), найденных внутри.
        """
        values = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}: {k}" if prefix else str(k)
                values.extend(flatten_scores(new_prefix, v))
        elif isinstance(obj, (int, float)):
            row[f"Quality {prefix}"] = obj  # prefix уже содержит [llm] + путь
            values.append(float(obj))
        return values

    for llm, eval_data in quality.items():
        if not isinstance(eval_data, dict):
            continue

        # 1) новый формат: {"justification": {...}}
        if "justification" in eval_data and isinstance(eval_data["justification"], dict):
            # запишем по ключам
            values = []
            for metric, value in eval_data["justification"].items():
                if isinstance(value, (int, float)):
                    row[f"Quality [{llm}] justification: {metric}"] = value
                    values.append(float(value))
            if values:
                model_score_sets[llm] = values
            continue

        # 2) старый формат эссе: {"essay_1": {...}, "essay_2": {...}, "average": {...}}
        # тут оставляем твою логику, но добавим fallback: если average нет — берём все найденные цифры
        values_for_model = []

        for section, section_data in eval_data.items():
            if isinstance(section_data, dict):
                for metric, value in section_data.items():
                    if isinstance(value, (int, float)):
                        row[f"Quality [{llm}] {section}: {metric}"] = value

                        # приоритетно средние значения
                        if section.lower() == "average":
                            values_for_model.append(float(value))
            elif isinstance(section_data, (int, float)):
                row[f"Quality [{llm}]: {section}"] = section_data
                values_for_model.append(float(section_data))

        # если не нашли average — доберём значения из всех секций
        if not values_for_model:
            # рекурсивно соберём все числа
            flat = []
            for section, section_data in eval_data.items():
                flat.extend(flatten_scores(f"[{llm}] {section}", section_data))
            values_for_model = flat

        if values_for_model:
            model_score_sets[llm] = values_for_model

    # --- Средний балл и приоритет ---
    # Берём "главную" модель: сначала yandex, иначе первую попавшуюся
    main_llm = None
    if "yandex" in model_score_sets:
        main_llm = "yandex"
    elif model_score_sets:
        main_llm = next(iter(model_score_sets.keys()))

    if main_llm:
        scores = model_score_sets[main_llm]
        avg_score = round(sum(scores) / len(scores), 2) if scores else None
    else:
        avg_score = None

    row["Average Score"] = avg_score
    row["Average Score Model"] = main_llm or ""

    if avg_score is None:
        row["Priority"] = "Не определён"
    elif avg_score < 4:
        row["Priority"] = "Низкий"
    elif avg_score < 7:
        row["Priority"] = "Средний"
    else:
        row["Priority"] = "Высокий"


    # --- Local Analysis full details ---
    local_analysis = data.get("local_analysis", {}) or {}
    row["Local Heuristic Score"] = local_analysis.get("heuristic_score", "")
    row["Local Prediction"] = local_analysis.get("ai_prediction", "")
    row["Local Verdict Comment"] = local_analysis.get("verdict_comment", "")
    details = local_analysis.get("details", {}) or {}
    for k, v in details.items():
        row[f"Local Feature: {k}"] = v

    return row

def export_all_to_excel():
    summaries = []
    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RESULTS_DIR, filename)
            try:
                summary = parse_result(filepath)
                summaries.append(summary)
            except Exception as e:
                print(f"⚠️ Ошибка при обработке {filename}: {e}")

    df = pd.DataFrame(summaries)

    if not df.empty:
        # --- Сортировка по среднему баллу ---
        df = df.sort_values(by="Average Score", ascending=False)

        # --- Перенос колонок (Average Score, Priority вперед) ---
        cols = ["Average Score", "Priority"] + [c for c in df.columns if c not in ["Average Score", "Priority"]]
        df = df[cols]

    df.to_excel(EXPORT_PATH, index=False)
    print(f"✅ Экспорт завершён: {EXPORT_PATH}")

if __name__ == "__main__":
    export_all_to_excel()
