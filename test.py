import jwt
import time
import requests
import json

# Загружаем ключ
with open("moduleAI/keys/authorized_key.json") as f:
    key_data = json.load(f)

private_key = key_data["private_key"]
service_account_id = key_data["service_account_id"]
key_id = key_data["id"]

now = int(time.time())

# Заголовок с обязательным "kid"
headers = {
    "kid": key_id,
    "alg": "PS256",
    "typ": "JWT"
}

# Полезная нагрузка (payload)
payload = {
    "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
    "iss": service_account_id,
    "iat": now,
    "exp": now + 360  # 6 минут жизни токена
}

# Генерируем JWT
encoded_jwt = jwt.encode(
    payload,
    private_key,
    algorithm="PS256",
    headers=headers
)

# Запрашиваем IAM токен
response = requests.post(
    "https://iam.api.cloud.yandex.net/iam/v1/tokens",
    headers={"Content-Type": "application/json"},
    json={"jwt": encoded_jwt}
)

# Выводим результат
print(response.status_code)
print(response.text)
