# tests/test_multi_qa.py

import requests
import json

def main():
    url = "http://127.0.0.1:8000/query"

    # مثال: عندي سياق بالإنجليزي، وأبغى الجواب بالعربي
    context = (
        "Max Verstappen dominated the Bahrain Grand Prix, building a strong "
        "lead early in the race. Behind him, Hamilton struggled with tyre wear "
        "in the final stint and had to manage his pace to keep the car on track."
    )

    question = "ليش هاملتون كان بطيء في نهاية السباق؟"

    payload = {
        "type": "multi_qa",
        "context": context,
        "question": question,
        "target_lang": "ar"   # نقدر نخليها 'en', 'fr', 'ar', ...
    }

    res = requests.post(url, json=payload)
    print("Status:", res.status_code)
    print("Response JSON:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()