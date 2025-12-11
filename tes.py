import requests

url = "https://open.bigmodel.cn/api/llm-application/open/knowledge"

payload = {
    "embedding_id": 3,
    "name": "test",
    "embedding_model": "Embedding-2",
    "contextual": 0,
    "description": "a test norDB",
    "background": "blue",
    "icon": "book"
}
headers = {
    "Authorization": "Bearer REMOVED_ZHIPU_API_KEY",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)