import os, requests
from dotenv import load_dotenv
load_dotenv()

class OpenAICompatClient:
    def __init__(self, base=None, key=None):
        self.base = base or os.getenv("LOCAL_OPENAI_BASE_URL","http://127.0.0.1:11434/v1")
        self.key  = key  or os.getenv("LOCAL_OPENAI_API_KEY","ollama")

    def chat(self, model, messages, temperature=0.2, max_tokens=2048):
        r = requests.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=600,
        )
        r.raise_for_status()
        return r.json()

# ---- Anthropic client (API) ----
import os
from anthropic import Anthropic

class AnthropicClient:
    def __init__(self, key=None):
        self.key = key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.key)

    def chat(self, model, messages, temperature=0.2, max_tokens=2048):
        # messages: [{"role":"user","content":"..."}]
        resp = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        # normalize to OpenAI-style
        text = "".join([b.text for b in resp.content if b.type == "text"])
        return {"choices":[{"message":{"content":text}}]}
