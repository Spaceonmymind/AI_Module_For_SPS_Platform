import g4f

def test_model_availability(model_name: str):
    prompt = "Скажи одно слово 'работает', если ты доступен."
    try:
        print(f"🔍 Проверка модели: {model_name}")
        response = g4f.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        print(f"✅ Ответ от {model_name}: {response[:100]}")
    except Exception as e:
        print(f"❌ Ошибка от {model_name}: {e}")

if __name__ == "__main__":
    test_model_availability("evil")