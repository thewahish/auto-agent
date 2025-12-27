from providers import OpenAICompatClient, AnthropicClient

class ModelRouter:
    def __init__(self):
        self.local = OpenAICompatClient()
        self.anthropic = AnthropicClient()
        self.models = {
            # local
            "general_local": "llama3.1",
            "code_qwen":     "qwen2.5-coder:7b",
            "code_ds":       "deepseek-coder:6.7b",
            "code_cl":       "codellama:7b-instruct",
            "code_sc":       "starcoder2:7b",
            # anthropic (API, paid)
            "claude_general": "claude-3-5-sonnet",
            "claude_code":    "claude-3-5-sonnet",   # Claude Code uses Claude models via API
        }

    def pick(self, tags:set[str]):
        # force Claude with tag
        if "claude" in tags or "premium" in tags:
            return ("anthropic", self.models["claude_code"] if "code" in tags else self.models["claude_general"])
        # local routing
        if {"code","refactor","tests"} & tags:
            if "alt" in tags:   return ("local", self.models["code_ds"])
            if "alt2" in tags:  return ("local", self.models["code_cl"])
            if "alt3" in tags:  return ("local", self.models["code_sc"])
            return ("local", self.models["code_qwen"])
        return ("local", self.models["general_local"])

    def chat(self, messages:list[dict], tags:set[str]):
        backend, model = self.pick(tags)
        client = self.anthropic if backend == "anthropic" else self.local
        return client.chat(model=model, messages=messages)
