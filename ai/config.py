import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "60.0"))

DEFAULT_WEIGHTS = {
    "price": 0.30,
    "delivery": 0.25,
    "quality": 0.20,
    "warranty": 0.10,
    "payment": 0.10,
    "compliance": 0.05,
}
