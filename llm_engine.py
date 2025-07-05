import requests
import json

import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

def call_ollama(prompt, model="mistral:latest"):
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=600
    )

    try:
        raw_lines = response.text.strip().splitlines()
        for line in raw_lines:
            try:
                data = json.loads(line)
                if "response" in data:
                    return data["response"]
            except json.JSONDecodeError:
                continue
        return "⚠️ Could not parse Ollama response."
    except Exception as e:
        return f"❌ Ollama call failed: {str(e)}"
