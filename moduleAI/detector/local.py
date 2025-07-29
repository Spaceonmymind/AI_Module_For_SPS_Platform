import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import re


class LocalAIDetector:
    def __init__(self, model_name="bert-base-uncased", device=None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def _split_sentences(self, text: str, max_len: int = 250) -> list[str]:
        # Простое разбиение по предложениям (можно заменить на nltk, spacy и т.п.)
        sentences = re.split(r'[.!?]\s+', text.strip())
        return [s.strip() for s in sentences if len(s.strip()) >= 10][:100]

    def detect(self, text: str) -> dict:
        sentences = self._split_sentences(text)
        scores = []

        for sentence in sentences:
            inputs = self.tokenizer(sentence, return_tensors="pt", truncation=True, max_length=512).to(self.device)
            with torch.no_grad():
                logits = self.model(**inputs).logits
                prob = torch.softmax(logits, dim=1)[0][1].item()  # [0]=real, [1]=AI
                scores.append((sentence, prob))

        probabilities = [p for _, p in scores]
        avg_prob = float(np.mean(probabilities))
        high_risk_snippets = [(s, round(p, 2)) for s, p in scores if p > 0.7]

        return {
            "average_ai_probability": round(avg_prob, 3),
            "likely_generated_snippets": high_risk_snippets,
            "repetition_score": self._repetition_score(text),
            "conclusion": self._generate_conclusion(avg_prob, len(high_risk_snippets))
        }

    def _repetition_score(self, text: str) -> float:
        # Оценка количества повторяющихся слов
        words = [w.lower() for w in re.findall(r'\w+', text)]
        if not words:
            return 0.0
        repeat_ratio = (len(words) - len(set(words))) / len(words)
        return round(repeat_ratio, 3)

    def _generate_conclusion(self, prob: float, risky_count: int) -> str:
        if prob > 0.75 and risky_count > 2:
            return "С высокой вероятностью текст сгенерирован ИИ."
        elif prob > 0.5:
            return "Возможно, в тексте присутствуют элементы генерации."
        else:
            return "Текст скорее всего написан человеком."
