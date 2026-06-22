"""
Nuclear Intelligence v4.0 - Ultra-LLM Engine ⚡
═══════════════════════════════════════════════════════════════════
Multi-Provider LLM with FREE providers chain:
AIMLAPI → DeepSeek → Groq → Gemini → Together → Fireworks → HuggingFace

Features:
- Intelligent routing with automatic fallback
- Response caching (LRU)
- Per-provider rate limiting
- Health monitoring & automatic degradation
- Structured JSON completion
- Token usage tracking
- Always-online optimized
═══════════════════════════════════════════════════════════════════
"""

import os
import json
import time
import hashlib
import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict
import re


# ─── Provider Definitions ───────────────────────────────────────

PROVIDERS: Dict[str, Dict] = {
    "aimlapi": {
        "name": "AIMLAPI GPT-4o", "env": "AIMLAPI_API_KEY",
        "base": "https://api.aimlapi.com/v1", "model": "gpt-4o",
        "priority": 0, "max_tokens": 16384, "context_window": 128000,
        "color": "🔵", "description": "GPT-4o Power"
    },
    "deepseek": {
        "name": "DeepSeek V3", "env": "DEEPSEEK_API_KEY",
        "base": "https://api.deepseek.com/v1", "model": "deepseek-chat",
        "priority": 1, "max_tokens": 64000, "context_window": 128000,
        "color": "🟢", "description": "Best free model, 128K context"
    },
    "groq": {
        "name": "Groq LPU", "env": "GROQ_API_KEY",
        "base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile",
        "priority": 2, "max_tokens": 8192, "context_window": 128000,
        "color": "⚡", "description": "Fastest inference, free tier"
    },
    "gemini": {
        "name": "Gemini 2.0", "env": "GEMINI_API_KEY",
        "base": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.0-flash",
        "priority": 3, "max_tokens": 8192, "context_window": 1000000,
        "color": "🟡", "description": "Google's fastest model"
    },
    "together": {
        "name": "Together AI", "env": "TOGETHER_API_KEY",
        "base": "https://api.together.xyz/v1", "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "priority": 4, "max_tokens": 4096, "context_window": 128000,
        "color": "🟠", "description": "Llama 3.3 70B"
    },
    "fireworks": {
        "name": "Fireworks AI", "env": "FIREWORKS_API_KEY",
        "base": "https://api.fireworks.ai/inference/v1", "model": "accounts/fireworks/models/deepseek-v3-0324",
        "priority": 5, "max_tokens": 32000, "context_window": 128000,
        "color": "🟣", "description": "DeepSeek V3 fast inference"
    },
    "huggingface": {
        "name": "HuggingFace", "env": "HF_TOKEN",
        "base": "https://api-inference.huggingface.co/models", "model": "Qwen/Qwen2.5-72B-Instruct",
        "priority": 10, "max_tokens": 2048, "context_window": 32768,
        "color": "🟤", "description": "Your HF token active"
    },
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


# ─── Main LLM Engine ─────────────────────────────────────────────

class LLMEngine:
    """Ultra-advanced multi-provider LLM engine with caching, rate limiting"""

    def __init__(
        self,
        provider_chain: Optional[List[str]] = None,
        default_temperature: float = 0.7,
        enable_caching: bool = True,
    ):
        self.provider_chain = provider_chain or [
            "aimlapi", "deepseek", "groq", "gemini", "together", 
            "fireworks", "huggingface"
        ]
        self.default_temperature = default_temperature
        self.enable_caching = enable_caching

        self._available_providers: List[str] = []
        self._stats: Dict[str, Any] = {
            "requests": 0, "successes": 0, "failures": 0,
            "by_provider": defaultdict(int),
            "total_tokens_used": 0,
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
        
        # SECURITY: never hardcode API keys. AIMLAPI must come from env / secrets only.
        # If missing, the provider is silently skipped (free-tier fallback still works).
        available = []
        for name in self.provider_chain:
            if name not in PROVIDERS:
                continue
            cfg = PROVIDERS[name]
            api_key = os.getenv(cfg["env"], "").strip()

            if not api_key or api_key in ("", "placeholder", "your_key_here", "hf_placeholder"):
                logger.debug(f"⏭️ {cfg['name']} - No API key")
                continue

            # Validate key format
            valid = True
            if name == "groq" and not api_key.startswith("gsk_"): valid = False
            if name == "deepseek" and not (api_key.startswith("sk-") or api_key.startswith("ghp_")): valid = False
            if name == "huggingface" and not api_key.startswith("hf_"): valid = False
            if name == "aimlapi" and len(api_key) < 20: valid = False

            if valid:
                available.append(name)
                self._provider_health[name] = {
                    "status": "available", "last_used": None, "failures": 0, "latency": 0
                }
                logger.info(f"✅ {cfg['color']} {cfg['name']} - {cfg['description']}")
            else:
                logger.warning(f"⚠️ {cfg['name']} - Invalid API key format")

        self._available_providers = available

        # Fallback to HF if no providers
        if not self._available_providers:
            hf_key = os.getenv("HF_TOKEN", "").strip()
            if hf_key and hf_key.startswith("hf_"):
                self._available_providers = ["huggingface"]
                logger.info("🔄 Falling back to HuggingFace inference API")
            else:
                logger.warning("❌ No LLM providers available! Add at least one API key to .env")
        
        logger.info(f"🎯 {len(self._available_providers)} providers ready")

    def _call_openai_compat(
        self, provider: str, messages: List[Dict], model: str, 
        temperature: float, max_tokens: int
    ) -> Optional[Dict]:
        """OpenAI-compatible API call"""
        try:
            from openai import OpenAI
            cfg = PROVIDERS[provider]
            api_key = os.getenv(cfg["env"])
            client = OpenAI(api_key=api_key, base_url=cfg["base"])
            
            response = client.chat.completions.create(
                model=model or cfg["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=min(max_tokens, cfg["max_tokens"]),
            )
            
            usage = response.usage or {}
            return {
                "content": response.choices[0].message.content,
                "provider": provider,
                "model": response.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens or 0,
                    "completion_tokens": usage.completion_tokens or 0,
                    "total_tokens": usage.total_tokens or 0,
                },
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            logger.debug(f"⚠️ {provider} failed: {e}")
            return None

    def _call_gemini(
        self, messages: List[Dict], model: str, 
        temperature: float, max_tokens: int
    ) -> Optional[Dict]:
        """Google Gemini API"""
        try:
            import requests
            cfg = PROVIDERS["gemini"]
            api_key = os.getenv(cfg["env"])
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
                f"{cfg['base']}/models/{model or cfg['model']}:generateContent?key={api_key}",
                json=payload, timeout=120
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "content": content,
                    "provider": "gemini",
                    "model": model or cfg["model"],
                    "usage": {"total_tokens": len(content) // 4},
                    "finish_reason": "stop",
                }
        except Exception as e:
            logger.debug(f"⚠️ Gemini failed: {e}")
        return None

    def _call_huggingface(
        self, messages: List[Dict], model: str,
        temperature: float, max_tokens: int
    ) -> Optional[Dict]:
        """HuggingFace Inference API"""
        try:
            import requests
            cfg = PROVIDERS["huggingface"]
            api_key = os.getenv(cfg["env"])
            hf_model = model or cfg["model"]

            # Build prompt
            prompt = "\n".join([
                f"{'System' if m['role']=='system' else m['role'].capitalize()}: {m['content']}"
                for m in messages
            ]) + "\nAssistant:"

            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": min(max_tokens, cfg["max_tokens"]),
                    "return_full_text": False,
                    "do_sample": temperature > 0.1,
                },
                "options": {"wait_for_model": True, "use_cache": True}
            }

            resp = requests.post(
                f"{cfg['base']}/{hf_model}",
                headers=headers, json=payload, timeout=180
            )

            if resp.status_code == 200:
                result = resp.json()
                content = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
                return {
                    "content": content.strip(),
                    "provider": "huggingface",
                    "model": hf_model,
                    "usage": {},
                    "finish_reason": "stop",
                }
            elif resp.status_code == 503:
                logger.info("⏳ HF model loading, waiting...")
                time.sleep(10)
                resp2 = requests.post(
                    f"{cfg['base']}/{hf_model}", headers=headers,
                    json={**payload, "options": {"wait_for_model": True}},
                    timeout=180
                )
                if resp2.status_code == 200:
                    result = resp2.json()
                    content = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
                    return {"content": content.strip(), "provider": "huggingface", "model": hf_model, "usage": {}}
        except Exception as e:
            logger.debug(f"⚠️ HuggingFace failed: {e}")
        return None

    def _call_provider(
        self, provider_name: str, messages: List[Dict], 
        model: Optional[str], temperature: float, max_tokens: int
    ) -> Optional[Dict]:
        """Dispatch to the appropriate provider"""
        start_time = time.time()
        result = None

        if provider_name == "gemini":
            result = self._call_gemini(messages, model, temperature, max_tokens)
        elif provider_name == "huggingface":
            result = self._call_huggingface(messages, model, temperature, max_tokens)
        elif provider_name in ("aimlapi", "deepseek", "groq", "together", "fireworks"):
            result = self._call_openai_compat(provider_name, messages, model, temperature, max_tokens)

        latency = time.time() - start_time

        if result:
            self.rate_limiter.record(provider_name)
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
        self, messages: List[Dict], model: Optional[str] = None,
        temperature: Optional[float] = None, max_tokens: int = 4096,
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
                    return cached

        errors = []
        for provider_name in self._available_providers:
            health = self._provider_health.get(provider_name, {})
            if health.get("failures", 0) > 5:
                continue

            for attempt in range(retry_count):
                result = self._call_provider(provider_name, messages, model, temperature, max_tokens)
                if result and result.get("content"):
                    self._stats["requests"] += 1
                    self._stats["successes"] += 1
                    self._stats["by_provider"][provider_name] += 1

                    usage = result.get("usage", {})
                    if isinstance(usage, dict):
                        self._stats["total_tokens_used"] += usage.get("total_tokens", 0)

                    self._current_provider_name = provider_name

                    if self.enable_caching and cache_key_prompt:
                        self.cache.set(cache_key_prompt, model or "default", temperature, result)

                    return result

                errors.append(f"{provider_name}: attempt {attempt + 1}")
                current_failures = self._provider_health.get(provider_name, {}).get("failures", 0) + 1
                self._provider_health[provider_name] = {
                    "status": "degraded", "last_error": datetime.now().isoformat(), "failures": current_failures,
                }
                time.sleep(0.5)

        self._stats["failures"] += 1
        self._last_error = "; ".join(errors[-3:])
        logger.warning(f"⚠️ All LLM providers failed: {self._last_error}")
        return None

    def chat(
        self, prompt: str, system_prompt: Optional[str] = None,
        temperature: Optional[float] = None, max_tokens: int = 4096,
    ) -> Optional[str]:
        """Simple chat completion"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = self._call_with_fallback(messages, temperature=temperature, max_tokens=max_tokens)
        return result["content"] if result else None

    def structured_completion(
        self, prompt: str, system_prompt: str,
        response_format: str = "json", temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> Optional[Dict]:
        """JSON-structured completion with automatic parsing"""
        json_instruction = (
            '\n\nIMPORTANT: Return ONLY valid JSON matching the schema exactly. '
            'No markdown code blocks, no explanation. Start with "{" and end with "}".'
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
                "text": content, "parsed": parsed, "provider": result["provider"],
                "model": result.get("model", ""), "usage": result.get("usage", {}), "parse_error": False,
            }

        # Try to extract JSON from text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {"text": content, "parsed": parsed, "provider": result["provider"], "parse_error": False}
            except: pass

        return {"text": content, "parsed": {}, "provider": result["provider"], "parse_error": True}

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response"""
        content = text.strip()

        # Remove markdown code blocks
        for marker in ["```json", "```yaml", "```"]:
            if marker in content:
                parts = content.split(marker)
                content = parts[1].strip() if len(parts) >= 2 else parts[0].replace("```", "").strip()
                break

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except: pass
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        cache_stats = self.cache.stats()
        total = self._stats["requests"]
        return {
            "requests": total, "successes": self._stats["successes"], "failures": self._stats["failures"],
            "by_provider": dict(self._stats["by_provider"]),
            "total_tokens_used": self._stats["total_tokens_used"],
            "success_rate": f"{(self._stats['successes'] / max(total, 1) * 100):.1f}%",
            "available_providers": self._available_providers,
            "current_provider": self._current_provider_name,
            "cache": cache_stats,
            "health": self._provider_health,
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check for all providers"""
        providers = {}
        for name in self.provider_chain:
            if name not in PROVIDERS:
                continue
            cfg = PROVIDERS[name]
            health = self._provider_health.get(name, {})
            failures = health.get("failures", 0)
            status = "healthy" if failures == 0 else "degraded" if failures < 5 else "unavailable"
            providers[cfg["name"]] = {
                "configured": name in self._available_providers,
                "status": status, "priority": cfg["priority"],
                "default_model": cfg["model"],
                "last_used": health.get("last_used"),
                "avg_latency": health.get("avg_latency"),
                "total_requests": self._stats["by_provider"].get(name, 0),
                "is_free": True,
            }
        return {
            "providers": providers,
            "active_provider": self._current_provider_name,
            "total_available": len(self._available_providers),
        }

    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("🧹 LLM cache cleared")