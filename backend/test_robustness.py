import requests
import time

url = "http://127.0.0.1:8000/summarize"
payload = {
    "text": "This is a test of the robust multi-model fallback system. It should try the Lite Preview model first, then Flash, then 1.5 Flash if needed.",
    "num_sentences": 1
}
headers = {"Content-Type": "application/json"}

print("Sending request to /summarize...")
start = time.time()
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        print(f"AI Summary: {data.get('ai_summary')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
print(f"Time taken: {time.time() - start:.2f}s")
