import json
import urllib.request
from typing import Optional, Dict, Any


class OllamaLLMProvider:
    """
    Interface for running 100% private, local LLMs via Ollama API (http://localhost:11434).
    Supports models like llama3.2, mistral, qwen2.5, deepseek-r1, phi3.
    """

    def __init__(self, host: str = "http://localhost:11434", model_name: str = "llama3.2"):
        self.host = host.rstrip("/")
        self.model_name = model_name

    def is_available(self) -> bool:
        """Checks if Ollama server is active and reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Sends generation request to Ollama REST endpoint.
        """
        if not self.is_available():
            return (
                "⚠️ Ollama is not currently running at http://localhost:11434.\n\n"
                "To run 100% local LLMs with Ollama:\n"
                "1. Download & install Ollama from https://ollama.com\n"
                f"2. Run in terminal: `ollama run {self.model_name}`\n"
                "3. Re-run this Personal RAG script!"
            )

        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            return f"⚠️ Ollama API Error: {str(e)}"
