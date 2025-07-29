import requests
import os


class GPTZeroDetector:
    def __init__(self):
        self.api_key = os.getenv("GPTZERO_API_KEY", "your-gptzero-api-key")
        self.api_url = os.getenv("GPTZERO_API_URL", "https://api.gptzero.me/v2/detect")

    def detect(self, text: str) -> str:
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {"document": text}
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            score = data['documents'][0]['average_generated_prob']
            return f"{float(score) * 100:.2f}% вероятность ИИ (GPTZero)"
        except Exception as e:
            return f"Ошибка GPTZero: {e}"
