def aggregate(struct, ai_det, fresh, analogs, quality):
    return {
        "structure_validation": struct,
        "ai_detection": ai_det,
        "freshness_check": fresh,
        "similar_ideas": analogs,
        "quality": quality,
        "verdict": {
            "ai_score": ai_det.get("score"),
            "is_ai": ai_det.get("verdict") in ("ai", True, 1),
            "quality_score": quality.get("score"),
            "is_recent": fresh.get("is_recent"),
        },
    }
