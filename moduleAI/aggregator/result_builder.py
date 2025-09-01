class ResultBuilder:
    """
    Формирует итоговый отчёт из всех этапов анализа.
    """

    def build(
            self,
            structure_report,
            ai_detection,
            outdated_fragments,
            similar_ideas,
            quality_scores,
            local_analysis
    ):
        return {
            "structure_validation": structure_report,
            "ai_detection": ai_detection,
            "freshness_check": outdated_fragments,
            "similar_ideas": similar_ideas,
            "quality_evaluation": quality_scores,
            "local_analysis": local_analysis
        }
