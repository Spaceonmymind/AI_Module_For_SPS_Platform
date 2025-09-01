import os
import json
import pandas as pd

RESULTS_DIR = "moduleAI/results"
EXPORT_PATH = "moduleAI/exported_summary.xlsx"

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
    for llm in ["yandex", "chatgpt"]:
        if llm in quality and isinstance(quality[llm], dict):
            for key, value in quality[llm].items():
                row[f"Quality [{llm}]: {key}"] = value

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
    df.to_excel(EXPORT_PATH, index=False)
    print(f"✅ Экспорт завершён: {EXPORT_PATH}")

if __name__ == "__main__":
    export_all_to_excel()
