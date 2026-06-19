"""
Nuclear Intelligence v4.0 - Ultra-LLM Engine ⚡
═══════════════════════════════════════════════════════════════════
Multi-Provider LLM with FREE providers chain:
DeepSeek → Groq → Gemini → Together → Fireworks → Cerebras → OpenRouter → Cloudflare → HuggingFace

Features:
- Intelligent routing with automatic fallback
- Response caching (LRU)
- Per-provider rate limiting
- Health monitoring & automatic degradation
- HuggingFace Inference API + Hub support
- Structured JSON completion
- Token usage tracking
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import time
import hashlib
import asyncio
import threading
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict
import re

# ─── Provider Definitions ───────────────────────────────────────

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
    context_window: int = 8192
    description: str = ""
    requires_account_id: bool = False
    is_free_tier: bool = True

PROVIDERS: Dict[str, LLMProvider] = {
    # ─── Tier 1: Best Free Models ⭐⭐⭐ ─────────────────────────
    "deepseek": LLMProvider(
        "DeepSeek V3", "DEEPSEEK_API_KEY",
        "https://api.deepseek.com/v1",
        "deepseek-chat", 1,
        rate_limit_rpm=60, max_tokens=64000, context_window=128000,
        description="🟢 DeepSeek V3 - Best free model, 128K context"
    ),
    "groq": LLMProvider(
        "Groq LPU", "GROQ_API_KEY",
        "https://api.groq.com/openai/v1",
        "llama-3.3-70b-versatile", 2,
        rate_limit_rpm=60, max_tokens=8192, context_window=128000,
        description="⚡ Groq - Fastest inference, Llama 3.3 70B"
    ),
    "cerebras": LLMProvider(
        "Cerebras", "CEREBRAS_API_KEY",
        "https://api.cerebras.ai/v1",
        "llama-3.3-70b", 3,
        rate_limit_rpm=60, max_tokens=4096, context_window=8192,
        description="🔵 Cerebras - Ultra-fast inference, free tier"
    ),
    # ─── Tier 2: Good Free Models ⭐⭐ ─────────────────────────
    "gemini": LLMProvider(
        "Google Gemini", "GEMINI_API_KEY",
        "https://generativelanguage.googleapis.com/v1beta",
        "gemini-2.0-flash", 4,
        rate_limit_rpm=60, max_tokens=8192, context_window=1000000,
        description="🔵 Gemini 2.0 Flash - Google's best free model"
    ),
    "fireworks": LLMProvider(
        "Fireworks AI", "FIREWORKS_API_KEY",
        "https://api.fireworks.ai/inference/v1",
        "accounts/fireworks/models/deepseek-v3-0324", 5,
        rate_limit_rpm=30, max_tokens=32000, context_window=128000,
        description="🟣 Fireworks AI - DeepSeek V3, fast inference"
    ),
    "together": LLMProvider(
        "Together AI", "TOGETHER_API_KEY",
        "https://api.together.xyz/v1",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo", 6,
        rate_limit_rpm=30, max_tokens=4096, context_window=128000,
        description="🟡 Together - Llama 3.3 70B, good quality"
    ),
    "novita": LLMProvider(
        "Novita AI", "NOVITA_API_KEY",
        "https://api.novita.ai/v3",
        "deepseek-ai/DeepSeek-V3", 7,
        rate_limit_rpm=30, max_tokens=64000, context_window=128000,
        description="🟣 Novita - DeepSeek V3, 128K context"
    ),
    # ─── Tier 3: Fallback Models ⭐ ─────────────────────────────
    "openrouter": LLMProvider(
        "OpenRouter", "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1",
        "deepseek/deepseek-chat-v3:free", 8,
        rate_limit_rpm=40, max_tokens=4096, context_window=64000,
        description="🟠 OpenRouter - Multiple free models"
    ),
    "cloudflare": LLMProvider(
        "Cloudflare AI", "CLOUDFLARE_API_KEY",
        "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run",
        "@cf/meta/llama-3.1-8b-instruct", 9,
        rate_limit_rpm=1000, max_tokens=4096, context_window=8192,
        description="⚪ Cloudflare - Workers AI, free daily",
        requires_account_id=True
    ),
    # ─── Tier 4: HuggingFace Inference ⭐ ───────────────────────
    "huggingface": LLMProvider(
        "HuggingFace", "HF_TOKEN",
        "https://api-inference.huggingface.co/models",
        "Qwen/Qwen2.5-72B-Instruct", 10,
        rate_limit_rpm=30, max_tokens=2048, context_window=32768,
        description="🟤 HuggingFace Inference API - Your token active!"
    ),
    "qalam_hf": LLMProvider(
        "Qalam HF Space", "HF_TOKEN",
        "https://huggingface.co/spaces/Qalam/Nuclear-Intelligence",
        "nuclear-intelligence", 11,
        rate_limit_rpm=30, max_tokens=4096, context_window=32768,
        description="⚛️ Qalam Nuclear Intelligence HF Space"
    ),
}


# ─── LRU Cache ──────────────────────────────────────────────────

class LRUCache:
    """Thread-safe LRU cache for LLM responses"""
    def __init__(self, max_size: int = 200):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        # Normalize prompt to first 500 chars for cache key
        normalized = prompt[:500].strip().lower()
        return hashlib.sha256(f"{normalized}:{model}:{temperature:.2f}".encode()).hexdigest()

    def get(self, prompt: str, model: str, temperature: float) -> Optional[Any]:
        key = self._make_key(prompt, model, temperature)
        with self._lock:
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
        with self._lock:
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            self.cache[key] = (value, datetime.now())

    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{(self.hits / max(total, 1) * 100):.1f}%",
            "size": len(self.cache),
            "max_size": self.max_size,
        }

    def clear(self):
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0


# ─── Rate Limiter ────────────────────────────────────────────────

class RateLimiter:
    """Per-provider rate limiting with sliding window"""
    def __init__(self):
        self.counters: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def can_request(self, provider: str, rpm: int) -> bool:
        now = datetime.now()
        with self._lock:
            self.counters[provider] = [
                t for t in self.counters[provider] if now - t < timedelta(minutes=1)
            ]
            return len(self.counters[provider]) < rpm

    def record(self, provider: str):
        now = datetime.now()
        with self._lock:
            self.counters[provider].append(now)

    def get_status(self, provider: str, rpm: int) -> Dict:
        now = datetime.now()
        with self._lock:
            recent = [t for t in self.counters[provider] if now - t < timedelta(minutes=1)]
        return {
            "requests_in_window": len(recent),
            "limit": rpm,
            "available": rpm - len(recent),
            "percentage": f"{(len(recent) / max(rpm, 1) * 100):.0f}%",
        }

    def clear(self, provider: str = None):
        with self._lock:
            if provider:
                self.counters[provider] = []
            else:
                self.counters.clear()


# ─── Main LLM Engine ─────────────────────────────────────────────

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
            "deepseek", "groq", "cerebras", "gemini", "fireworks",
            "together", "novita", "openrouter", "cloudflare", "huggingface"
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
        self._current_provider_name: Optional[str] = None
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
            if not api_key or api_key in ("", "placeholder", "your_key_here", "hf_placeholder"):
                logger.debug(f"⏭️ {provider.name} - No API key")
                continue

            # Skip if requires account_id but it's missing
            if provider.requires_account_id:
                account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
                if not account_id:
                    logger.debug(f"⏭️ {provider.name} - No account ID")
                    continue

            # Validate key format
            if self._validate_key(name, api_key):
                available.append(name)
                self._provider_health[name] = {
                    "status": "available",
                    "last_used": None,
                    "failures": 0,
                    "avg_latency": 0,
                    "total_calls": 0,
                }
                logger.info(f"✅ {provider.description}")
            else:
                logger.warning(f"⚠️ {provider.name} - Invalid API key format")

        self._available_providers = available

        # If no providers, try HF token as fallback
        if not self._available_providers:
            hf_key = os.getenv("HF_TOKEN", "").strip()
            if hf_key and (hf_key.startswith("hf_") or len(hf_key) > 20):
                self._available_providers = ["huggingface"]
                logger.info("🔄 Falling back to HuggingFace inference API")
            else:
                logger.error("❌ No LLM providers available! Add at least one API key to .env")
        else:
            logger.info(f"🎯 {len(self._available_providers)} providers ready: {', '.join(self._available_providers)}")

    def _validate_key(self, provider: str, api_key: str) -> bool:
        """Provider-specific key format validation"""
        if len(api_key) < 10:
            return False
        if provider == "groq" and not api_key.startswith("gsk_"):
            return False
        if provider == "deepseek" and not (api_key.startswith("sk-") or api_key.startswith("ghp_")):
            return False
        if provider == "huggingface" and not api_key.startswith("hf_"):
            return False
        return True

    @property
    def _current_provider(self):
        return self._current_provider_name

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
                headers=headers, json=payload, timeout=180
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

    def _call_cerebras(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Cerebras API - Ultra-fast inference"""
        try:
            from openai import OpenAI
            provider = PROVIDERS["cerebras"]
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
                "provider": "cerebras",
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.warning(f"⚠️ Cerebras failed: {e}")
        return None

    def _call_gemini(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Google Gemini API"""
        try:
            import requests
            provider = PROVIDERS["gemini"]
            api_key = os.getenv(provider.api_key_env)
            actual_model = model or provider.default_model
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
                logger.warning(f"⚠️ Gemini error: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed: {e}")
        return None

    def _call_fireworks(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Optional[Dict]:
        """Fireworks AI API"""
        try:
            from openai import OpenAI
            provider = PROVIDERS["fireworks"]
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
                "provider": "fireworks",
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.warning(f"⚠️ Fireworks failed: {e}")
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
                headers=headers, json=payload, timeout=180
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
        """HuggingFace Inference API - Enhanced with better model detection"""
        try:
            import requests
            provider = PROVIDERS["huggingface"]
            api_key = os.getenv(provider.api_key_env)
            hf_model = model or provider.default_model

            # Build prompt
            prompt = self._build_hf_prompt(messages)

            headers = {"Authorization": f"Bearer {api_key}"}

            # Try chat completions format first (for chat models)
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": min(max_tokens, provider.max_tokens),
                    "return_full_text": False,
                    "do_sample": temperature > 0.1,
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": True,
                }
            }

            resp = requests.post(
                f"{provider.api_base}/{hf_model}",
                headers=headers,
                json=payload,
                timeout=180
            )

            if resp.status_code == 200:
                result = resp.json()
                content = ""
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    content = result.get("generated_text", str(result))
                else:
                    content = str(result)

                # Clean up response
                content = content.strip()

                return {
                    "content": content,
                    "provider": "huggingface",
                    "model": hf_model,
                    "usage": {"total_tokens": len(prompt) // 4 + len(content) // 4},
                    "finish_reason": "stop",
                }
            elif resp.status_code == 503:
                # Model loading - try again with wait
                logger.info("⏳ HuggingFace model loading, waiting...")
                time.sleep(10)
                resp2 = requests.post(
                    f"{provider.api_base}/{hf_model}",
                    headers=headers,
                    json={**payload, "options": {"wait_for_model": True}},
                    timeout=180
                )
                if resp2.status_code == 200:
                    result = resp2.json()
                    content = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
                    return {
                        "content": content.strip(),
                        "provider": "huggingface",
                        "model": hf_model,
                        "usage": {},
                        "finish_reason": "stop",
                    }
            else:
                logger.warning(f"⚠️ HuggingFace error: {resp.status_code} - {resp.text[:150]}")

        except Exception as e:
            logger.warning(f"⚠️ HuggingFace failed: {e}")
        return None

    def _build_hf_prompt(self, messages: List[Dict]) -> str:
        """Build HF-compatible prompt from messages"""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
        parts.append("Assistant:")
        return "\n".join(parts)

    # ─── Provider Dispatcher ─────────────────────────────────────

    def _call_provider(self, provider_name: str, messages: List[Dict], model: Optional[str], temperature: float, max_tokens: int) -> Optional[Dict]:
        """Dispatch to the appropriate provider"""
        if self.enable_rate_limiting:
            provider = PROVIDERS.get(provider_name)
            if provider and not self.rate_limiter.can_request(provider_name, provider.rate_limit_rpm):
                logger.debug(f"⏳ Rate limited: {provider_name}")
                return None

        start_time = time.time()
        calls = {
            "deepseek": lambda: self._call_deepseek(messages, model, temperature, max_tokens),
            "groq": lambda: self._call_groq(messages, model, temperature, max_tokens),
            "cerebras": lambda: self._call_cerebras(messages, model, temperature, max_tokens),
            "gemini": lambda: self._call_gemini(messages, model, temperature, max_tokens),
            "fireworks": lambda: self._call_fireworks(messages, model, temperature, max_tokens),
            "together": lambda: self._call_together(messages, model, temperature, max_tokens),
            "novita": lambda: self._call_novita(messages, model, temperature, max_tokens),
            "openrouter": lambda: self._call_openrouter(messages, model, temperature, max_tokens),
            "cloudflare": lambda: self._call_cloudflare(messages, model, temperature, max_tokens),
            "huggingface": lambda: self._call_huggingface(messages, model, temperature, max_tokens),
        }

        result = calls.get(provider_name, lambda: None)()
        latency = time.time() - start_time

        if result:
            if self.enable_rate_limiting:
                self.rate_limiter.record(provider_name)

            # Update health with latency tracking
            health = self._provider_health.get(provider_name, {})
            total_calls = health.get("total_calls", 0) + 1
            avg_lat = health.get("avg_latency", 0)
            new_avg = (avg_lat * (total_calls - 1) + latency) / total_calls

            self._provider_health[provider_name] = {
                "status": "active",
                "last_used": datetime.now().isoformat(),
                "failures": 0,
                "avg_latency": round(new_avg, 2),
                "total_calls": total_calls,
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

        # Check cache first
        if self.enable_caching:
            cache_key_prompt = messages[-1]["content"] if messages else ""
            if len(cache_key_prompt) < 1000:
                cached = self.cache.get(cache_key_prompt, model or "default", temperature)
                if cached:
                    logger.debug("📦 Cache hit!")
                    self._stats["cache_hits"] = self._stats.get("cache_hits", 0) + 1
                    return cached

        errors = []

        for provider_name in self._available_providers:
            health = self._provider_health.get(provider_name, {})
            if health.get("failures", 0) > 5:
                continue  # Skip degraded providers

            for attempt in range(retry_count):
                result = self._call_provider(provider_name, messages, model, temperature, max_tokens)
                if result and result.get("content"):
                    self._stats["requests"] += 1
                    self._stats["successes"] += 1
                    self._stats["by_provider"][provider_name] += 1

                    usage = result.get("usage", {})
                    if isinstance(usage, dict):
                        total = usage.get("total_tokens", 0)
                    else:
                        total = 0
                    self._stats["total_tokens_used"] += total

                    self._current_provider_name = provider_name

                    if self.enable_caching and cache_key_prompt:
                        self.cache.set(cache_key_prompt, model or "default", temperature, result)

                    return result

                errors.append(f"{provider_name}: attempt {attempt + 1} failed")
                current_failures = self._provider_health.get(provider_name, {}).get("failures", 0) + 1
                self._provider_health[provider_name] = {
                    "status": "degraded",
                    "last_error": datetime.now().isoformat(),
                    "failures": current_failures,
                }
                time.sleep(1)

        self._stats["failures"] += 1
        self._last_error = "; ".join(errors[-3:])
        logger.error(f"❌ All LLM providers failed: {self._last_error}")
        return None

    # ─── Public API ─────────────────────────────────────────────

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

        # Add JSON enforcement to system prompt
        json_instruction = (
            "\n\nIMPORTANT: Return ONLY valid JSON matching the schema exactly. "
            "No markdown code blocks, no explanation, no text before or after the JSON."
            'Start with "{" and end with "}".'
        )

        messages = [
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": prompt},
        ]

        result = self._call_with_fallback(messages, temperature=temperature or 0.2, max_tokens=max_tokens)
        if not result:
            return None

        content = result["content"].strip()

        # Parse JSON
        parsed = self._parse_json_response(content)
        if parsed:
            return {
                "text": content,
                "parsed": parsed,
                "provider": result["provider"],
                "model": result.get("model", ""),
                "usage": result.get("usage", {}),
                "parse_error": False,
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
            "error_detail": "Failed to parse JSON from response",
        }

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response with multiple strategies"""
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

        # Try finding JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        cache_stats = self.cache.stats()
        total = self._stats["requests"]
        return {
            "requests": total,
            "successes": self._stats["successes"],
            "failures": self._stats["failures"],
            "by_provider": dict(self._stats["by_provider"]),
            "total_tokens_used": self._stats["total_tokens_used"],
            "success_rate": f"{(self._stats['successes'] / max(total, 1) * 100):.1f}%",
            "available_providers": self._available_providers,
            "current_provider": self._current_provider,
            "last_error": self._last_error,
            "cache": cache_stats,
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
            failures = health.get("failures", 0)
            status = "healthy" if failures == 0 else "degraded" if failures < 5 else "unavailable"
            providers[provider.name] = {
                "configured": name in self._available_providers,
                "status": status,
                "priority": provider.priority,
                "default_model": provider.default_model,
                "rate_limit": rate_status,
                "last_used": health.get("last_used"),
                "avg_latency": health.get("avg_latency"),
                "total_requests": self._stats["by_provider"].get(name, 0),
                "is_free": provider.is_free_tier,
                "context_window": provider.context_window,
            }
        return {
            "providers": providers,
            "active_provider": self._current_provider,
            "total_available": len(self._available_providers),
            "total_configured": len([p for p in self.provider_chain if p in PROVIDERS]),
        }

    def get_best_available(self) -> Optional[str]:
        """Get the best available provider"""
        return self._get_best_provider()

    def reset_health(self, provider: str = None):
        """Reset health status for a provider or all providers"""
        if provider:
            if provider in self._provider_health:
                self._provider_health[provider] = {"status": "available", "failures": 0}
        else:
            for name in self._provider_health:
                self._provider_health[name] = {"status": "available", "failures": 0}

    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("🧹 LLM cache cleared")