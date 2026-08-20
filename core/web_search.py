"""Nuclear Intelligence - Web Search Engine - Free providers"""
import os
import time
from collections import OrderedDict
from typing import List, Dict, Any
from loguru import logger

class WebSearchEngine:
    def __init__(self):
        self.serp_key = os.getenv("SERP_API_KEY", "")
        self._search_count = 0
        self._cache_ttl = max(30, int(os.getenv("WEB_SEARCH_CACHE_TTL_SECONDS", "900")))
        self._cache_size = max(8, int(os.getenv("WEB_SEARCH_CACHE_SIZE", "128")))
        self._cache: OrderedDict[tuple[str, int], tuple[float, List[Dict[str, Any]]]] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    def search(self, query: str, num_results: int = 8) -> List[Dict[str, Any]]:
        normalized = " ".join((query or "").split()).lower()
        key = (normalized, max(1, min(int(num_results), 20)))
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self._cache_ttl:
            self._cache_hits += 1
            self._cache.move_to_end(key)
            return [dict(item) for item in cached[1]]
        self._cache_misses += 1
        self._search_count += 1
        results = self._search_duckduckgo(normalized, key[1])
        if not results and self.serp_key:
            results = self._search_serpapi(normalized, key[1])
        self._cache[key] = (now, [dict(item) for item in results])
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return results

    def stats(self) -> Dict[str, Any]:
        total = self._cache_hits + self._cache_misses
        return {
            "requests": self._search_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": round(self._cache_hits / total, 4) if total else 0.0,
            "cache_entries": len(self._cache),
            "cache_ttl_seconds": self._cache_ttl,
        }

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        # Try the modern `ddgs` package first (it replaced `duckduckgo_search`),
        # then fall back to the legacy `duckduckgo_search` import path.
        try:
            from ddgs import DDGS  # type: ignore
            ddgs_mod = "ddgs"
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # type: ignore
                ddgs_mod = "duckduckgo_search"
            except ImportError:
                return self._search_duckduckgo_fallback(query, num_results)
        try:
            with DDGS() as ddgs:
                results = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", "") or r.get("href", ""),
                        "snippet": r.get("body", "") or r.get("snippet", ""),
                        "source": "duckduckgo",
                    }
                    for r in ddgs.text(query, max_results=num_results)
                ]
                if results:
                    logger.info(f"DuckDuckGo ({ddgs_mod}): {len(results)} results")
                return results
        except Exception as e:
            logger.debug(f"DuckDuckGo failed: {e}")
        return self._search_duckduckgo_fallback(query, num_results)

    def _search_duckduckgo_fallback(self, query: str, num_results: int) -> List[Dict]:
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0"}
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                results = []
                for result in soup.select(".result")[:num_results]:
                    title_elem = result.select_one(".result__title a")
                    snippet_elem = result.select_one(".result__snippet")
                    if title_elem:
                        results.append({"title": title_elem.get_text(strip=True), "url": title_elem.get("href",""), "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "", "source": "duckduckgo"})
                return results
        except Exception as e: logger.debug(f"DuckDuckGo fallback failed: {e}")
        return []

    def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        try:
            import requests
            params = {"q": query, "api_key": self.serp_key, "num": num_results, "engine": "google"}
            resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return [{"title": i.get("title",""), "url": i.get("link",""), "snippet": i.get("snippet",""), "source": "google_serpapi"} for i in data.get("organic_results",[])[:num_results]]
        except Exception as e: logger.debug(f"SerpAPI failed: {e}")
        return []
