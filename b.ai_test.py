import requests

response = requests.post(
    "https://api.b.ai/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-oymwnd880z0uvdo8wmhhob67cs8f5o6s",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-5.2",
        "messages": [
            {"role": "user", "content": "Hello World"}
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 1000,
    },
)

print(response.text)