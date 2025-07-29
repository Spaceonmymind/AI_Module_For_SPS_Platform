from models.input import IdeaInput
from parser.text_parser import TextParser
from validator.structure_validator import StructureValidator
from detector.ai_detector import AIDetector
from relevance.freshness_checker import FreshnessChecker
from similarity.analogue_finder import AnalogueFinder
from evaluator.quality_evaluator import QualityEvaluator
from aggregator.result_builder import ResultBuilder



class TextAnalysisPipeline:
    def __init__(self):
        self.parser = TextParser()
        self.validator = StructureValidator()
        self.detector = AIDetector()
        self.freshness = FreshnessChecker()
        self.similarity = AnalogueFinder()
        self.evaluator = QualityEvaluator()
        self.aggregator = ResultBuilder()


    def run(self, idea: IdeaInput):
        sections = self.parser.parse(idea.text)
        structure_report = self.validator.validate(sections)
        ai_detection = self.detector.detect(idea.text)
        outdated_fragments = self.freshness.check(idea.text)
        similar_ideas = self.similarity.find(idea.text)
        quality_scores = self.evaluator.evaluate(idea.text)

        final_result = self.aggregator.build(
            structure_report=structure_report,
            ai_detection=ai_detection,
            outdated_fragments=outdated_fragments,
            similar_ideas=similar_ideas,
            quality_scores=quality_scores
        )
        return final_result
