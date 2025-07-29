import os
import json
import pandas as pd

RESULTS_DIR = "moduleAI/results"
EXPORT_PATH = "moduleAI/exported_summary.xlsx"

def parse_result(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # AI Detection
    detection = data.get("ai_detection", {})
    gptzero = detection.get("sources", {}).get("gptzero", "")
    yandex_ai = detection.get("sources", {}).get("yandex", "")
    chatgpt_ai = detection.get("sources", {}).get("chatgpt", "")
    local = detection.get("sources", {}).get("local", {})
    verdict = detection.get("verdict", "")

    # Freshness
    freshness = data.get("freshness_check", {})
    freshness_yandex = freshness.get("yandex", "")
    freshness_chatgpt = freshness.get("chatgpt", "")

    # Similar ideas
    similar = data.get("similar_ideas", {})
    similar_yandex = similar.get("yandex", "")
    similar_chatgpt = similar.get("chatgpt", "")

    # Quality
    quality = data.get("quality_evaluation", {})
    quality_yandex = quality.get("yandex", {})
    quality_chatgpt = quality.get("chatgpt", {})

    # Result
    return {
        "Файл": os.path.basename(filepath),
        "Вердикт": verdict,

        "GPTZero": gptzero,
        "Yandex AI": yandex_ai,
        "ChatGPT AI": chatgpt_ai,
        "Local AI %": local.get("average_ai_probability", ""),
        "Local Repetition": local.get("repetition_score", ""),
        "Local Conclusion": local.get("conclusion", ""),

        "Freshness Yandex": freshness_yandex,
        "Freshness ChatGPT": freshness_chatgpt,

        "Similar Yandex": similar_yandex,
        "Similar ChatGPT": similar_chatgpt,

        "Ясность (chatgpt)": quality_chatgpt.get("ясность", ""),
        "Удобство (chatgpt)": quality_chatgpt.get("удобство", ""),
        "Выгода (chatgpt)": quality_chatgpt.get("выгода", ""),
        "Масштабируемость (chatgpt)": quality_chatgpt.get("масштабируемость", ""),

        "Ясность (yandex)": quality_yandex.get("ясность", ""),
        "Удобство (yandex)": quality_yandex.get("удобство", ""),
        "Выгода (yandex)": quality_yandex.get("выгода", ""),
        "Масштабируемость (yandex)": quality_yandex.get("масштабируемость", ""),
    }


def export_all_to_excel():
    summaries = []

    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RESULTS_DIR, filename)
            summary = parse_result(filepath)
            summaries.append(summary)

    df = pd.DataFrame(summaries)
    df.to_excel(EXPORT_PATH, index=False)
    print(f"✅ Экспорт завершён: {EXPORT_PATH}")

if __name__ == "__main__":
    export_all_to_excel()
