from yandexcloud import SDK
import json
from pathlib import Path
import requests
import jwt
import time

def get_iam_token_from_json_key(path_to_key="/Users/egorgladkih/PycharmProjects/AI_Module_For_SPS_Platform/moduleAI/keys/authorized_key.json") -> str:

    with open(path_to_key, "r") as f:
        key_data = json.load(f)

    private_key = key_data["private_key"]
    service_account_id = key_data["service_account_id"]
    key_id = key_data["id"]

    now = int(time.time())
    payload = {
        "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        "iss": service_account_id,
        "iat": now,
        "exp": now + 360
    }

    headers = {
        "kid": key_id,
        "alg": "PS256",
        "typ": "JWT"
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="PS256", headers=headers)

    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        headers={"Content-Type": "application/json"},
        json={"jwt": encoded_jwt}
    )

    response.raise_for_status()
    return response.json()["iamToken"]