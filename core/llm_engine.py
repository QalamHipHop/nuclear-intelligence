"""Nuclear Intelligence - Multi-Provider LLM Engine - FREE PROVIDERS"""
import os, json, time
from typing import List, Dict, Any, Optional
from loguru import logger
from dataclasses import dataclass

@dataclass
class LLMProvider:
    name: str; api_key_env: str; api_base: str; default_model: str
    priority: int; enabled: bool = True; rate_limit_rpm: int = 60

PROVIDERS = {
    "groq": LLMProvider("Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", 1, rate_limit_rpm=60),
    "together": LLMProvider("Together AI", "TOGETHER_API_KEY", "https://api.together.xyz/v1", "meta-llama/Llama-3.1-8B-Instruct-Turbo", 2, rate_limit_rpm=30),
    "cloudflare": LLMProvider("Cloudflare", "CLOUDFLARE_API_KEY", "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run", "@cf/meta/llama-3.1-8b-instruct", 3, rate_limit_rpm=120),
    "openrouter": LLMProvider("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "meta-llama/llama-3.1-8b-instruct", 4, rate_limit_rpm=40),
    "huggingface": LLMProvider("HuggingFace", "HF_TOKEN", "https://api-inference.huggingface.co/models", "Qwen/Qwen2.5-7B-Instruct", 5, rate_limit_rpm=30),
}

class LLMEngine:
    def __init__(self, provider_chain: Optional[List[str]] = None, default_temperature: float = 0.7):
        self.provider_chain = provider_chain or ["groq", "together", "cloudflare", "openrouter", "huggingface"]
        self.default_temperature = default_temperature
        self._available_providers = []
        self._stats = {"requests": 0, "successes": 0, "failures": 0, "by_provider": {}}
        self._current_provider = None
        self._init_providers()

    def _init_providers(self):
        for name in self.provider_chain:
            if name not in PROVIDERS: continue
            provider = PROVIDERS[name]
            api_key = os.getenv(provider.api_key_env)
            if api_key and api_key not in ("", "placeholder", "gsr_placeholder", "tk_placeholder", "sk-or-placeholder", "hf_placeholder"):
                self._available_providers.append(name)
                logger.info(f"✅ {provider.name} available")
            else:
                logger.debug(f"⏭️ {provider.name} not configured")

    def _call_with_fallback(self, messages: List[Dict], model: Optional[str] = None,
                            temperature: Optional[float] = None, max_tokens: int = 2048, retry_count: int = 2) -> Optional[Dict]:
        temperature = temperature if temperature is not None else self.default_temperature
        errors = []

        for provider_name in self._available_providers:
            for attempt in range(retry_count):
                try:
                    if provider_name in ("groq", "together", "openrouter"):
                        from openai import OpenAI
                        provider = PROVIDERS[provider_name]
                        api_key = os.getenv(provider.api_key_env)
                        base_url = None
                        if provider_name == "together": base_url = "https://api.together.xyz/v1"
                        if provider_name == "openrouter": base_url = "https://openrouter.ai/api/v1"
                        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
                        actual_model = model or provider.default_model
                        self._stats["requests"] += 1
                        response = client.chat.completions.create(
                            model=actual_model, messages=messages,
                            temperature=temperature, max_tokens=max_tokens,
                        )
                        self._stats["successes"] += 1
                        self._stats["by_provider"][provider_name] = self._stats["by_provider"].get(provider_name, 0) + 1
                        self._current_provider = provider_name
                        return {"content": response.choices[0].message.content, "provider": provider_name, "model": actual_model, "usage": dict(response.usage) if response.usage else {}, "finish_reason": response.choices[0].finish_reason}
                except Exception as e:
                    logger.warning(f"⚠️ {PROVIDERS[provider_name].name} failed: {str(e)[:80]}")
                    errors.append(f"{provider_name}: {str(e)[:60]}")
                    time.sleep(1)

        # HuggingFace fallback
        hf_key = os.getenv("HF_TOKEN")
        if hf_key and hf_key not in ("", "hf_placeholder"):
            try:
                import requests
                hf_model = model or PROVIDERS["huggingface"].default_model
                headers = {"Authorization": f"Bearer {hf_key}"}
                prompt = "\n".join([f"{'System' if m['role']=='system' else m['role'].capitalize()}: {m['content']}" for m in messages]) + "\nAssistant:"
                resp = requests.post(f"https://api-inference.huggingface.co/models/{hf_model}", headers=headers, json={"inputs": prompt, "parameters": {"temperature": temperature, "max_new_tokens": max_tokens}}, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    content = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
                    self._stats["successes"] += 1
                    return {"content": content, "provider": "huggingface", "model": hf_model, "usage": {}, "finish_reason": "stop"}
            except Exception as e:
                logger.warning(f"⚠️ HuggingFace fallback failed: {str(e)[:80]}")

        logger.error(f"❌ All LLM providers failed: {errors}")
        self._stats["failures"] += 1
        return None

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 2048) -> Optional[str]:
        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        result = self._call_with_fallback(messages, temperature=temperature, max_tokens=max_tokens)
        return result["content"] if result else None

    def structured_completion(self, prompt: str, system_prompt: str, response_format: str = "json", temperature: Optional[float] = None) -> Optional[Dict]:
        import re
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        result = self._call_with_fallback(messages, temperature=temperature or 0.3, max_tokens=2048)
        if not result: return None
        content = result["content"]
        for marker in ["```json", "```", "```yaml"]:
            if marker in content:
                parts = content.split(marker)
                if len(parts) >= 3: content = parts[1].strip()
                elif len(parts) == 2: content = parts[1].replace("```","").strip()
                break
        try:
            return {"text": content, "parsed": json.loads(content), "provider": result["provider"], "model": result["model"]}
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try: return {"text": content, "parsed": json.loads(json_match.group()), "provider": result["provider"], "model": result["model"]}
                except: pass
            return {"text": content, "parsed": {}, "provider": result["provider"], "model": result["model"], "parse_error": True}

    def get_stats(self) -> Dict[str, Any]:
        return {**self._stats, "available_providers": self._available_providers, "current_provider": self._current_provider, "success_rate": f"{(self._stats['successes'] / max(self._stats['requests'], 1) * 100):.1f}%"}

    def health_check(self) -> Dict[str, Any]:
        return {"providers": {PROVIDERS[p].name: {"status": "available", "priority": PROVIDERS[p].priority} for p in self._available_providers}, "active_provider": self._current_provider}
