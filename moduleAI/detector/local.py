import re
import os
import torch
from collections import Counter
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


class LocalAIDetector:
    def __init__(self):
        dict_path = os.path.join(os.path.dirname(__file__), "dictionary")

        def load_words(filename):
            path = os.path.join(dict_path, filename)
            with open(path, encoding="utf-8") as f:
                return set(line.strip().lower() for line in f if line.strip())

        self.too_high_vocab = load_words("too_high_vocab.txt")
        self.markers = load_words("list_markers.txt")
        self.intro_words = load_words("intro_words.txt")
        self.agreement_preps = load_words("agreement_prepositions.txt")

        self.sentiment_classifier = pipeline("text-classification", model="blanchefort/rubert-base-cased-sentiment")
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")

    def detect(self, text: str) -> dict:
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        def tokens_divergence(sentences):
            amount = 0
            count = len(sentences)
            for s in sentences:
                tokens = s.split()
                amount += len(tokens) - 1 if '-' in tokens else len(tokens)
            mean = amount / count
            divergence = sum(((len(s.split()) - 1 if '-' in s else len(s.split())) - mean) ** 2 for s in sentences)
            return 1 if (divergence / count) ** 0.5 < 8.93 else 0

        def avg_token_length(sentences):
            sum_len, count = 0, 0
            for s in sentences:
                for token in s.split():
                    if len(token) > 2:
                        sum_len += len(token)
                        count += 1
            avg = sum_len / count if count else 0
            return 1 if avg > 7.67 else 0

        def emotions(text):
            result = self.sentiment_classifier(text[:512])[0]
            label, score = result['label'], result['score']
            return 1 if (score if label == 'neutral' else 1 - score) >= 0.20 else 0

        def connection(sentences):
            return 1 if len(sentences) > 25 else 0

        def number_of_words(sentences):
            total = sum(len(s.split()) for s in sentences)
            avg = total / len(sentences) if sentences else 0
            return (1 if avg < 21.67 else 0), total

        def tabs(text):
            blocks = text.split('\n')
            tab_count = len(blocks)
            _, total_words = number_of_words(sentences)
            return 1 if tab_count / total_words > 0.03 else 0

        def tires(text):
            dash = text.count("—") + text.count("–")
            _, total_words = number_of_words(sentences)
            return 1 if dash / total_words > 0.0071 else 0

        def quotes(text):
            q = text.count("\"") / 2
            _, total_words = number_of_words(sentences)
            return 1 if (q / total_words if total_words else 0) > 0.0057 else 0

        def brackets(text):
            b = text.count("(")
            _, total_words = number_of_words(sentences)
            return 1 if (b / total_words if total_words else 0) > 0.0046 else 0

        def slashs(text):
            return 0 if text.count("/") >= 1 else 1

        def points(text):
            p = text.count(":")
            _, total_words = number_of_words(sentences)
            return 1 if (p / total_words if total_words else 0) >= 0.0009 else 0

        def keywords(text):
            phrases = ["Таким образом", "Кроме того", "все вышеперечисленное", "Благодаря", "заключается"]
            count = sum(text.lower().count(p.lower()) for p in phrases)
            return 1 if count > 3 else 0.9 if count == 2 else 0.8 if count == 1 else 0

        def high_vocab(text):
            words = re.findall(r'\b\w+\b', text.lower())
            count = sum(1 for w in words if w in self.too_high_vocab)
            return min(count / len(words), 1.0) if words else 0

        def logic_markers(text):
            count = sum(text.lower().count(m) for m in self.markers)
            return min(count / 10, 1.0)

        def intro_words_score(text):
            words = re.findall(r'\b\w+\b', text.lower())
            count = sum(1 for w in words if w in self.intro_words)
            return min(count / len(words), 1.0) if words else 0

        def prep_density(text):
            text_lower = text.lower()
            count = sum(text_lower.count(prep) for prep in self.agreement_preps)
            total_words = len(text.split())
            return min(count / total_words, 1.0) if total_words else 0

        def pronoun_frequency(text):
            pronouns = {"я", "мы", "мой", "наша", "мне", "нам", "нас", "меня", "моё", "моей"}
            tokens = text.lower().split()
            count = sum(1 for token in tokens if token in pronouns)
            return min(count / len(tokens), 1.0) if tokens else 0

        def comma_density(text):
            sentences = re.split(r'[.!?]', text)
            commas = text.count(',')
            return min(commas / len(sentences), 1.0) if sentences else 0

        def repetition_score(text):
            words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
            counts = Counter(words)
            most_common = counts.most_common(5)
            total = sum(counts.values())
            rep_score = sum(freq for _, freq in most_common) / total if total else 0
            return min(rep_score, 1.0)

        # Метрики
        k1 = tokens_divergence(sentences)
        k2 = avg_token_length(sentences)
        k3, total_words = number_of_words(sentences)
        k4 = tabs(text)
        k5 = emotions(text)
        k6 = connection(sentences)
        k7 = tires(text)
        k8 = quotes(text)
        k9 = brackets(text)
        k10 = slashs(text)
        k11 = points(text)
        k12 = keywords(text)
        k13 = high_vocab(text)
        k14 = logic_markers(text)
        k15 = intro_words_score(text)
        k16 = prep_density(text)
        k17 = pronoun_frequency(text)
        k18 = comma_density(text)
        k19 = repetition_score(text)

        scores = [k1, k2, k3, k4, k5, k6, k7, k8, k9, k10,
                  k11, k12, k13, k14, k15, k16, k17, k18, k19]
        weights = [1, 1, 1, 1, 0.3, 1, 1, 1, 1, 1,
                   1, 1, 1.2, 1, 1, 0.8, 1, 0.8, 1.2]

        heuristic_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            ai_score = probs[0][1].item()

        prediction = 1 if ai_score > 0.5 or heuristic_score > 0.55 else 0

        reasons = []
        if ai_score > 0.65:
            reasons.append(f"высокая оценка DistilBERT ({round(ai_score, 2)})")
        if k2:
            reasons.append("длинные слова")
        if k6:
            reasons.append("плохая связанность предложений")
        if k7 or k8:
            reasons.append("высокая плотность тире/кавычек")
        if k12 > 0.8:
            reasons.append("шаблонные фразы")
        if k13 > 0.01:
            reasons.append("термины из высокого словаря")
        if k14 > 0.3:
            reasons.append("много логических маркеров")
        if k15 > 0.01:
            reasons.append("вводные конструкции")
        if k16 > 0.04:
            reasons.append("перегрузка грамматическими предлогами")
        if k17 < 0.002:
            reasons.append("отсутствие личных местоимений")
        if k18 > 0.7:
            reasons.append("избыточное количество запятых")
        if k19 > 0.12:
            reasons.append("повторы слов")

        comment = (
            "Текст, вероятно, сгенерирован ИИ. Это подтверждается: " + ", ".join(reasons) + "."
            if prediction else
            "Текст, вероятно, написан человеком. Ни один из признаков явно не указывает на ИИ-происхождение."
        )

        return {
            "heuristic_score": round(heuristic_score, 4),
            "ai_probability_distilbert": round(ai_score, 4),
            "ai_prediction": prediction,
            "verdict_comment": comment,
            "details": {
                "tokens_divergence": k1,
                "avg_token_length": k2,
                "short_sentences": k3,
                "tabs_density": k4,
                "neutrality": k5,
                "sentence_connection": k6,
                "dash_density": k7,
                "quotes_density": k8,
                "bracket_density": k9,
                "no_slash": k10,
                "colon_density": k11,
                "keywords_score": k12,
                "vocab_density": round(k13, 4),
                "logic_markers": round(k14, 4),
                "intro_words": round(k15, 4),
                "prep_density": round(k16, 4),
                "pronoun_freq": round(k17, 4),
                "comma_density": round(k18, 4),
                "repetition_score": round(k19, 4),
            }
        }
