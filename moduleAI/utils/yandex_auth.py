import os
import json
import requests
import jwt
import time
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения (.env)
load_dotenv()

def get_iam_token_from_json_key() -> str:
    """
    Получение IAM-токена из авторизованного ключа сервисного аккаунта.
    Сначала ищет путь в .env (YANDEX_KEY_FILE),
    если нет — использует дефолтный moduleAI/keys/authorized_key.json.
    """

    # 1. Берём путь из .env
    key_path = os.getenv("YANDEX_KEY_FILE")

    # 2. Если не задан — используем дефолт
    if not key_path:
        key_path = Path(__file__).resolve().parent.parent / "keys" / "authorized_key.json"

    key_path = Path(key_path)

    # 3. Проверка существования
    print(f"🔍 Ищу ключ по пути: {key_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"❌ Файл ключа не найден: {key_path}")

    # 4. Читаем JSON с ключом
    with open(key_path, "r", encoding="utf-8") as f:
        key_data = json.load(f)

    private_key = key_data["private_key"]
    service_account_id = key_data["service_account_id"]
    key_id = key_data["id"]

    # 5. Формируем JWT
    now = int(time.time())
    payload = {
        "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        "iss": service_account_id,
        "iat": now,
        "exp": now + 360  # 6 минут
    }

    headers = {
        "kid": key_id,
        "alg": "PS256",
        "typ": "JWT"
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="PS256", headers=headers)

    # 6. Запрашиваем IAM-токен
    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        headers={"Content-Type": "application/json"},
        json={"jwt": encoded_jwt}
    )

    response.raise_for_status()
    token = response.json()["iamToken"]

    print("✅ IAM-токен успешно получен (обрезан):", token[:40] + "...")
    return token
