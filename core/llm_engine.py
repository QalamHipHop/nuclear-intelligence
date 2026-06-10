"""
Nuclear Intelligence v3.0 - Ultra-LLM Engine
═══════════════════════════════════════════════════════════════════
Multi-Provider LLM with FREE providers chain:
DeepSeek → Groq → Gemini → Together → OpenRouter → Cloudflare → HuggingFace
Intelligent routing, caching, fallback, and rate limiting
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import time
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict

# ─── Provider Definitions ─────────────────────────────────────────

@dataclass
class LLMProvider:
    name: str
    api_key_env: str
    api_base: str
    default_model: str
    priority: int
    enabled: bool = True
    rate_limit_rpm: int = 60
    supports_structured: bool = True
    max_tokens: int = 4096
    description: str = ""

PROVIDERS: Dict[str, LLMProvider] = {
    # ─── Tier 1: Best Free Models ───────────────────────────────
    "deepseek": LLMProvider(
        "DeepSeek V3", "DEEPSEEK_API_KEY",
        "https://api.deepseek.com/v1",
        "deepseek-chat",
        1, rate_limit_rpm=60, max_tokens=64000,
        description="🟢 DeepSeek V3 - Best free model, 128K context"
    ),
    "groq": LLMProvider(
        "Groq LPU", "GROQ_API_KEY",
        "https://api.groq.com/openai/v1",
        "llama-3.3-70b-versatile",
        2, rate_limit_rpm=60, max_tokens=8192,
        description="⚡ Groq - Fastest inference, Llama 3.3 70B"
    ),
    "gemini": LLMProvider(
        "Google Gemini", "GEMINI_API_KEY",
        "https://generativelanguage.googleapis.com/v1beta",
        "gemini-2.0-flash",
        3, rate_limit_rpm=60, max_tokens=8192,
        description="🔵 Gemini 2.0 Flash - Google's best free model"
    ),
    # ─── Tier 2: Good Free Models ───────────────────────────────
    "together": LLMProvider(
        "Together AI", "TOGETHER_API_KEY",
        "https://api.together.xyz/v1",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        4, rate_limit_rpm=30, max_tokens=4096,
        description="🟡 Together - Llama 3.3 70B, good quality"
    ),
    "openrouter": LLMProvider(
        "OpenRouter", "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1",
        "deepseek/deepseek-chat-v3:free",
        5, rate_limit_rpm=40, max_tokens=4096,
        description="🟠 OpenRouter - Multiple free models"
    ),
    "novita": LLMProvider(
        "Novita AI", "NOVITA_API_KEY",
        "https://api.novita.ai/v3",
        "deepseek-ai/DeepSeek-V3",
        6, rate_limit_rpm=30, max_tokens=64000,
        description="🟣 Novita - DeepSeek V3, 128K context"
    ),
    # ─── Tier 3: Fallback Models ────────────────────────────────
    "cloudflare": LLMProvider(
        "Cloudflare AI", "CLOUDFLARE_API_KEY",
        "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run",
        "@cf/meta/llama-3.1-8b-instruct",
        7, rate_limit_rpm=1000, max_tokens=4096,
        description="⚪ Cloudflare - Workers AI, 1000/day"
    ),
    "huggingface": LLMProvider(
        "HuggingFace", "HF_TOKEN",
        "https://api-inference.huggingface.co/models",
        "Qwen/Qwen2.5-72B-Instruct",
        8, rate_limit_rpm=30, max_tokens=4096,
        description="🟤 HuggingFace - Your existing token"
    ),
}


class LRUCache:
    """Simple LRU cache for LLM responses"""
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        return hashlib.sha256(f"{prompt[:500]}:{model}:{temperature}".encode()).hexdigest()

    def get(self, prompt: str, model: str, temperature: float) -> Optional[Any]:
        key = self._make_key(prompt, model, temperature)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(hours=2):
                self.hits += 1
                return value
            del self.cache[key]
        self.misses += 1
        return None

    def set(self, prompt: str, model: str, temperature: float, value: Any):
        key = self._make_key(prompt, model, temperature)
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest]
        self.cache[key] = (value, datetime.now())

    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{(self.hits/max(total,1)*100):.1f}%",
            "size": len(self.cache)
        }


class RateLimiter:
    """Per-provider rate limiting"""
    def __init__(self):
        self.counters: Dict[str, List[datetime]] = defaultdict(list)

    def can_request(self, provider: str, rpm: int) -> bool:
        now = datetime.now()
        self.counters[provider] = [
            t for t in self.counters[provider]
            if now - t < timedelta(minutes=1)
        ]
        return len(self.counters[provider]) < rpm

    def record(self, provider: str):
        self.counters[provider].append(datetime.now())

    def get_status(self, provider: str, rpm: int) -> Dict:
        now = datetime.now()
        recent = [t for t in self.counters[provider] if now - t < timedelta(minutes=1)]
        return {
            "requests_in_window": len(recent),
            "limit": rpm,
            "available": rpm - len(recent),
            "percentage": f"{(len(recent)/max(rpm,1)*100):.0f}%"
        }


class LLMEngine:
    """Ultra-advanced multi-provider LLM engine with caching, rate limiting, and intelligent routing"""

    def __init__(
        self,
        provider_chain: Optional[List[str]] = None,
        default_temperature: float = 0.7,
        enable_caching: bool = True,
        enable_rate_limiting: bool = True,
    ):
        # Priority order: Best free models first
        self.provider_chain = provider_chain or [
            "deepseek", "groq", "gemini", "together",
            "openrouter", "novita", "cloudflare", "huggingface"
        ]
        self.default_temperature = default_temperature
        self.enable_caching = enable_caching
        self.enable_rate_limiting = enable_rate_limiting

        self._available_providers: List[str] = []
        self._stats: Dict[str, Any] = {
            "requests": 0, "successes": 0, "failures": 0,
            "by_provider": defaultdict(int),
            "total_tokens_used": 0,
            "cache_stats": {},
        }
        self._current_provider: Optional[str] = None
        self._last_error: Optional[str] = None
        self._provider_health: Dict[str, Dict] = {}

        self.cache = LRUCache(max_size=200)
        self.rate_limiter = RateLimiter()

        self._init_providers()

    def _init_providers(self):
        """Check which providers have valid API keys"""
        logger.info("🔍 Checking LLM providers...")
        available = []
        for name in self.provider_chain:
            if name not in PROVIDERS:
                continue
            provider = PROVIDERS[name]
            api_key = os.getenv(provider.api_key_env, "").strip()

            # Skip placeholder/invalid keys
            if not api_key or api_key in ("", "placeholder", "your_key_here"):
                logger.debug(f"⏭️ {provider.name} - No API key configured")
                continue

            # Validate key format
            if self._validate_key(name, api_key):
                available.append(name)
                self._provider_health[name] = {"status": "available", "last_used": None, "failures": 0}
                logger.info(f"✅ {provider.description}")
            else:
                logger.warning(f"⚠️ {provider.name} - Invalid API key")

        self._available_providers = available

        if not self._available_providers:
            logger.error("❌ No LLM providers available! Add at least one API key to .env")
            # Fallback to HuggingFace if only HF token is available
            hf_key = os.getenv("HF_TOKEN", "").strip()
            if hf_key and hf_key not in ("", "hf_placeholder"):
                self._available_providers = ["huggingface"]
                logger.info("🔄 Falling back to HuggingFace inference")
        else:
            logger.info(f"🎯 {len(self._available_providers)} providers ready: {', '.join(self._available_providers)}")

    def _validate_key(self, provider: str, api_key: str) -> bool:
        """Basic key format validation"""
        if len(api_key) < 10:
            return False
        # Provider-specific validation
        if provider == "groq" and not api_key.startswith("gsk_"):
            return False
        if provider == "deepseek" and not api_key.startswith("sk-"):
            return False
        return True

    def _get_best_provider(self) -> Optional[str]:
        """Get the best available provider based on priority and health"""
        for name in self._available_providers:
            health = self._provider_health.get(name, {})
            if health.get("failures", 0) < 3:
                return name
        return self._available_providers[0] if self._available_providers else None

    # ─── Provider-specific API Calls ───────────────────────────

    def _call_deepseek(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """DeepSeek API - Best free model with 128K context"""
        try:
            import requests
            provider = PROVIDERS["deepseek"]
            api_key = os.getenv(provider.api_key_env)
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model or provider.default_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": min(max_tokens, provider.max_tokens),
                "stream": False
            }
            resp = requests.post(
                f"{provider.api_base}/chat/completions",
                headers=headers, json=payload, timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                usage = data.get("usage", {})
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "provider": "deepseek",
                    "model": data.get("model"),
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }
            elif resp.status_code == 429:
                self._provider_health["deepseek"]["failures"] = self._provider_health.get("deepseek", {}).get("failures", 0) + 1
                logger.warning("⏳ DeepSeek rate limited")
            else:
                logger.warning(f"⚠️ DeepSeek error: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek call failed: {e}")
        return None

    def _call_groq(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Groq API - Fastest inference"""
        try:
            from openai import OpenAI
            provider = PROVIDERS["groq"]
            api_key = os.getenv(provider.api_key_env)
            client = OpenAI(api_key=api_key, base_url=provider.api_base)
            response = client.chat.completions.create(
                model=model or provider.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=min(max_tokens, provider.max_tokens),
            )
            usage = response.usage or {}
            return {
                "content": response.choices[0].message.content,
                "provider": "groq",
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.warning(f"⚠️ Groq failed: {e}")
        return None

    def _call_gemini(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Google Gemini API"""
        try:
            import requests
            provider = PROVIDERS["gemini"]
            api_key = os.getenv(provider.api_key_env)
            actual_model = model or provider.default_model
            # Convert OpenAI format to Gemini format
            contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": min(max_tokens, 8192),
                }
            }
            resp = requests.post(
                f"{provider.api_base}/models/{actual_model}:generateContent?key={api_key}",
                json=payload, timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "content": content,
                    "provider": "gemini",
                    "model": actual_model,
                    "usage": {"total_tokens": len(content) // 4},
                    "finish_reason": "stop",
                }
            else:
                logger.warning(f"⚠️ Gemini error: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed: {e}")
        return None

    def _call_together(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Together AI API"""
        try:
            from openai import OpenAI
            provider = PROVIDERS["together"]
            client = OpenAI(api_key=os.getenv(provider.api_key_env), base_url=provider.api_base)
            response = client.chat.completions.create(
                model=model or provider.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=min(max_tokens, provider.max_tokens),
            )
            usage = response.usage or {}
            return {
                "content": response.choices[0].message.content,
                "provider": "together",
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.warning(f"⚠️ Together failed: {e}")
        return None

    def _call_openrouter(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """OpenRouter API"""
        try:
            from openai import OpenAI
            provider = PROVIDERS["openrouter"]
            client = OpenAI(api_key=os.getenv(provider.api_key_env), base_url=provider.api_base)
            response = client.chat.completions.create(
                model=model or provider.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=min(max_tokens, provider.max_tokens),
            )
            usage = response.usage or {}
            return {
                "content": response.choices[0].message.content,
                "provider": "openrouter",
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.warning(f"⚠️ OpenRouter failed: {e}")
        return None

    def _call_novita(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Novita AI API"""
        try:
            import requests
            provider = PROVIDERS["novita"]
            api_key = os.getenv(provider.api_key_env)
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model or provider.default_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": min(max_tokens, provider.max_tokens),
            }
            resp = requests.post(
                f"{provider.api_base}/chat/completions",
                headers=headers, json=payload, timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "provider": "novita",
                    "model": data.get("model"),
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }
            else:
                logger.warning(f"⚠️ Novita error: {resp.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Novita failed: {e}")
        return None

    def _call_cloudflare(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Cloudflare Workers AI"""
        try:
            import requests
            account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
            api_key = os.getenv("CLOUDFLARE_API_KEY", "")
            if not account_id or not api_key:
                return None
            provider = PROVIDERS["cloudflare"]
            headers = {"Authorization": f"Bearer {api_key}"}
            prompt = "\n".join([
                f"{'System' if m['role']=='system' else m['role'].capitalize()}: {m['content']}"
                for m in messages
            ]) + "\nAssistant:"
            resp = requests.post(
                provider.api_base.replace("{account_id}", account_id) + f"/{model or provider.default_model}",
                headers=headers,
                json={"messages": [{"role": "user", "content": prompt}], "max_tokens": min(max_tokens, 4096)},
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "content": data.get("result", {}).get("response", ""),
                    "provider": "cloudflare",
                    "model": model or provider.default_model,
                    "usage": {},
                    "finish_reason": "stop",
                }
        except Exception as e:
            logger.warning(f"⚠️ Cloudflare failed: {e}")
        return None

    def _call_huggingface(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """HuggingFace Inference API - Using your token"""
        try:
            import requests
            provider = PROVIDERS["huggingface"]
            api_key = os.getenv(provider.api_key_env)
            hf_model = model or provider.default_model
            headers = {"Authorization": f"Bearer {api_key}"}
            prompt = "\n".join([
                f"{'System' if m['role']=='system' else m['role'].capitalize()}: {m['content']}"
                for m in messages
            ]) + "\nAssistant:"
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{hf_model}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": min(max_tokens, provider.max_tokens),
                        "return_full_text": False,
                    }
                },
                timeout=120
            )
            if resp.status_code == 200:
                result = resp.json()
                content = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
                return {
                    "content": content,
                    "provider": "huggingface",
                    "model": hf_model,
                    "usage": {},
                    "finish_reason": "stop",
                }
            elif resp.status_code == 503:
                logger.warning("⏳ HuggingFace model loading...")
                time.sleep(5)
            else:
                logger.warning(f"⚠️ HuggingFace error: {resp.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ HuggingFace failed: {e}")
        return None

    # ─── Main Call Handler ───────────────────────────────────────

    def _call_provider(self, provider_name: str, messages: List[Dict], model: Optional[str], temperature: float, max_tokens: int) -> Optional[Dict]:
        """Dispatch to the appropriate provider"""
        if self.enable_rate_limiting:
            provider = PROVIDERS.get(provider_name)
            if provider and not self.rate_limiter.can_request(provider_name, provider.rate_limit_rpm):
                logger.debug(f"⏳ Rate limited: {provider_name}")
                return None

        calls = {
            "deepseek": lambda: self._call_deepseek(messages, model, temperature, max_tokens),
            "groq": lambda: self._call_groq(messages, model, temperature, max_tokens),
            "gemini": lambda: self._call_gemini(messages, model, temperature, max_tokens),
            "together": lambda: self._call_together(messages, model, temperature, max_tokens),
            "openrouter": lambda: self._call_openrouter(messages, model, temperature, max_tokens),
            "novita": lambda: self._call_novita(messages, model, temperature, max_tokens),
            "cloudflare": lambda: self._call_cloudflare(messages, model, temperature, max_tokens),
            "huggingface": lambda: self._call_huggingface(messages, model, temperature, max_tokens),
        }

        result = calls.get(provider_name, lambda: None)()
        if result:
            if self.enable_rate_limiting:
                self.rate_limiter.record(provider_name)
            self._provider_health[provider_name] = {
                "status": "active",
                "last_used": datetime.now().isoformat(),
                "failures": 0,
            }
        return result

    def _call_with_fallback(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        retry_count: int = 2,
    ) -> Optional[Dict]:
        """Try providers in priority order with automatic fallback"""
        temperature = temperature if temperature is not None else self.default_temperature

        # Check cache first (only for non-structured calls)
        cache_key_prompt = messages[-1]["content"] if messages else ""
        if self.enable_caching and len(cache_key_prompt) < 1000:
            cached = self.cache.get(cache_key_prompt, model or "default", temperature)
            if cached:
                logger.debug("📦 Cache hit!")
                return cached

        errors = []

        for provider_name in self._available_providers:
            # Reset failures after a few successes
            health = self._provider_health.get(provider_name, {})
            if health.get("failures", 0) > 5:
                continue

            for attempt in range(retry_count):
                result = self._call_provider(provider_name, messages, model, temperature, max_tokens)
                if result:
                    self._stats["requests"] += 1
                    self._stats["successes"] += 1
                    self._stats["by_provider"][provider_name] += 1

                    usage = result.get("usage", {})
                    total = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0
                    self._stats["total_tokens_used"] += total

                    self._current_provider = provider_name

                    if self.enable_caching and cache_key_prompt:
                        self.cache.set(cache_key_prompt, model or "default", temperature, result)

                    return result

                errors.append(f"{provider_name}: attempt {attempt + 1} failed")
                self._provider_health[provider_name] = {
                    "status": "degraded",
                    "last_error": datetime.now().isoformat(),
                    "failures": health.get("failures", 0) + 1,
                }
                time.sleep(1)

        self._stats["failures"] += 1
        self._last_error = "; ".join(errors[-3:])
        logger.error(f"❌ All LLM providers failed: {self._last_error}")
        return None

    # ─── Public API ──────────────────────────────────────────────

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """Simple chat completion"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = self._call_with_fallback(messages, temperature=temperature, max_tokens=max_tokens)
        return result["content"] if result else None

    def structured_completion(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str = "json",
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> Optional[Dict]:
        """JSON-structured completion with automatic parsing"""
        import re

        messages = [
            {"role": "system", "content": system_prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no markdown, no explanation."},
            {"role": "user", "content": prompt},
        ]

        result = self._call_with_fallback(messages, temperature=temperature or 0.3, max_tokens=max_tokens)
        if not result:
            return None

        content = result["content"].strip()

        # Parse JSON from response
        parsed = self._parse_json_response(content)
        if parsed:
            return {
                "text": content,
                "parsed": parsed,
                "provider": result["provider"],
                "model": result.get("model", ""),
                "usage": result.get("usage", {}),
            }

        # Try to extract JSON from text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "text": content,
                    "parsed": parsed,
                    "provider": result["provider"],
                    "model": result.get("model", ""),
                    "parse_error": False,
                }
            except:
                pass

        return {
            "text": content,
            "parsed": {},
            "provider": result["provider"],
            "model": result.get("model", ""),
            "parse_error": True,
        }

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response"""
        content = text.strip()

        # Remove markdown code blocks
        for marker in ["```json", "```yaml", "```"]:
            if marker in content:
                parts = content.split(marker)
                if len(parts) >= 3:
                    content = parts[1].strip()
                elif len(parts) == 2:
                    content = parts[1].replace("```", "").strip()
                break

        # Try direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try finding JSON in text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        return {
            "requests": self._stats["requests"],
            "successes": self._stats["successes"],
            "failures": self._stats["failures"],
            "by_provider": dict(self._stats["by_provider"]),
            "total_tokens_used": self._stats["total_tokens_used"],
            "success_rate": f"{(self._stats['successes'] / max(self._stats['requests'], 1) * 100):.1f}%",
            "available_providers": self._available_providers,
            "current_provider": self._current_provider,
            "last_error": self._last_error,
            "cache": self.cache.stats(),
            "health": self._provider_health,
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check for all providers"""
        providers = {}
        for name in self.provider_chain:
            if name not in PROVIDERS:
                continue
            provider = PROVIDERS[name]
            health = self._provider_health.get(name, {})
            rate_status = self.rate_limiter.get_status(name, provider.rate_limit_rpm) if self.enable_rate_limiting else {}
            providers[provider.name] = {
                "configured": name in self._available_providers,
                "status": "healthy" if health.get("failures", 0) == 0 else "degraded" if health.get("failures", 0) < 5 else "unavailable",
                "priority": provider.priority,
                "default_model": provider.default_model,
                "rate_limit": rate_status,
                "last_used": health.get("last_used"),
                "total_requests": self._stats["by_provider"].get(name, 0),
            }
        return {
            "providers": providers,
            "active_provider": self._current_provider,
            "total_available": len(self._available_providers),
        }

    def get_best_available(self) -> Optional[str]:
        """Get the best available provider"""
        return self._get_best_provider()