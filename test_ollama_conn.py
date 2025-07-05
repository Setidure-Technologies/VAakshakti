import requests
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/tags"

try:
    response = requests.get(OLLAMA_URL, timeout=10)
    response.raise_for_status() # Raise an exception for HTTP errors
    print(f"Successfully connected to Ollama. Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: Could not connect to Ollama at {OLLAMA_URL}. Error: {e}")
except requests.exceptions.Timeout:
    print(f"Timeout Error: Request to Ollama at {OLLAMA_URL} timed out.")
except requests.exceptions.RequestException as e:
    print(f"Request Error: An error occurred during the request to Ollama at {OLLAMA_URL}. Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")