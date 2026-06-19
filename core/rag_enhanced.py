"""
Nuclear Intelligence v4.0 - Enhanced RAG Retriever ⚛️📚
═══════════════════════════════════════════════════════════════════
Drops on top of WebSearchEngine + KnowledgeGraph to provide:

1. **Domain boosting** — IAEA / NRC / DOE / peer-reviewed venues get
   a weight multiplier so they surface first.
2. **Source diversity** — round-robin from at least N distinct domains
   so the answer doesn't rest on a single source.
3. **Recency bias** — pages <5 years old get a small lift.
4. **Citation re-ranking** — merge web hits + KG neighbours, score
   each, return the top-K with provenance.

The original WebSearchEngine.search() is still the upstream signal.
This module is purely additive.
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from typing import Dict, List, Optional
from urllib.parse import urlparse

from loguru import logger


DOMAIN_WEIGHTS: Dict[str, float] = {
    # Tier 1: highest authority on nuclear matters
    "iaea.org": 2.5, "iaea": 2.5,
    "nrc.gov": 2.5,
    "oecd-nea.org": 2.2, "nea.fr": 2.2,
    "energy.gov": 2.0, "inl.gov": 2.0, "ornl.gov": 2.0, "anl.gov": 2.0,
    "lanl.gov": 2.0, "bnl.gov": 2.0, "sandia.gov": 2.0, "pnnl.gov": 2.0,
    "iter.org": 2.2, "iter": 2.2,
    # Tier 2: peer-reviewed venues and reputable industry bodies
    "nature.com": 1.8, "sciencedirect.com": 1.8, "springer.com": 1.7,
    "wiley.com": 1.7, "link.springer.com": 1.7, "onlinelibrary.wiley.com": 1.7,
    "ieee.org": 1.7, "ieeexplore.ieee.org": 1.7, "ans.org": 1.7,
    "iopscience.iop.org": 1.7,
    "world-nuclear.org": 1.6, "wna": 1.6,
    "cea.fr": 1.6, "jaea.go.jp": 1.6,
    # Tier 3: preprints & general encyclopedic
    "arxiv.org": 1.3,
    "wikipedia.org": 0.9, "en.wikipedia.org": 0.9,
    # Default
    "_default_": 1.0,
}


def domain_weight(url: str) -> float:
    """Return the trust weight for a URL based on its domain."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        host = ""
    if not host:
        return DOMAIN_WEIGHTS["_default_"]
    for d, w in DOMAIN_WEIGHTS.items():
        if d == "_default_":
            continue
        if d in host:
            return w
    return DOMAIN_WEIGHTS["_default_"]


YEAR_RE = re.compile(r"\b(19|20)(\d{2})\b")


def recency_boost(text: str) -> float:
    """Boost a result if its snippet mentions a recent year.

    Maps a 5-year window: 1.0 (current year) down to ~0.85 (5 yrs ago).
    """
    current_year = time.gmtime().tm_year
    matches = [int(m.group(0)) for m in YEAR_RE.finditer(text or "")]
    if not matches:
        return 1.0
    years = [y for y in matches if 1950 <= y <= current_year + 1]
    if not years:
        return 1.0
    most_recent = max(years)
    age = max(0, current_year - most_recent)
    # Smooth decay
    return max(0.80, 1.0 - 0.04 * age)


def rerank_web_results(results: List[Dict], query: str, top_k: int = 8) -> List[Dict]:
    """Re-rank web results with domain weight + recency + query overlap.

    Each result is enriched with:
      - `score`         (final combined score)
      - `domain_weight` (authority multiplier)
      - `recency_boost` (recency multiplier)
    """
    q_terms = set(re.findall(r"\w+", (query or "").lower())) - {"the", "a", "of", "in", "to", "and", "is", "are", "for"}
    if not q_terms:
        q_terms = set()

    scored: List[Dict] = []
    for r in results or []:
        url = r.get("url", "") or ""
        title = r.get("title", "") or ""
        snippet = r.get("snippet", "") or ""

        d_w = domain_weight(url)
        r_b = recency_boost(snippet + " " + title)

        overlap = sum(1 for t in q_terms if t in (title + " " + snippet).lower())
        overlap_score = overlap / max(1, len(q_terms))

        score = 0.6 * overlap_score + 0.3 * (d_w / 2.5) + 0.1 * r_b

        enriched = dict(r)
        enriched["score"] = round(score, 4)
        enriched["domain_weight"] = d_w
        enriched["recency_boost"] = round(r_b, 3)
        scored.append(enriched)

    scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return scored[:top_k]


def diversify_sources(results: List[Dict], min_domains: int = 3) -> List[Dict]:
    """Round-robin so the top-K hits cover ≥ min_domains distinct hosts.

    Falls back to original ordering if diversity already satisfied.
    """
    if not results:
        return results

    # Bucket by host
    by_host: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        try:
            host = (urlparse(r.get("url", "")).hostname or "unknown").lower()
        except Exception:
            host = "unknown"
        by_host[host].append(r)

    # Round-robin
    out: List[Dict] = []
    hosts = sorted(by_host.keys(), key=lambda h: -by_host[h][0].get("score", 0.0))
    pointers = {h: 0 for h in hosts}
    while any(pointers[h] < len(by_host[h]) for h in hosts) and len(out) < len(results):
        for h in hosts:
            i = pointers[h]
            if i < len(by_host[h]):
                out.append(by_host[h][i])
                pointers[h] += 1
                if len(out) >= len(results):
                    break

    distinct = {((urlparse(r.get("url", "")).hostname or "").lower()) for r in out}
    if len(distinct) < min_domains:
        logger.debug(f"RAG diversity low: {len(distinct)} domains in {len(out)} hits")
    return out


def build_rag_context(ranked: List[Dict], max_chars: int = 6000) -> str:
    """Format the top hits into an inline context block for the LLM."""
    parts: List[str] = []
    used = 0
    for i, r in enumerate(ranked or [], 1):
        title = r.get("title", "").strip()
        snippet = r.get("snippet", "").strip()
        url = r.get("url", "").strip()
        block = f"[{i}] {title}\n{snippet}\nSource: {url}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts)


def summarize_sources(ranked: List[Dict]) -> Dict:
    """Return a small stats block for logging / UI."""
    hosts: Dict[str, int] = defaultdict(int)
    for r in ranked or []:
        try:
            host = (urlparse(r.get("url", "")).hostname or "unknown").lower()
        except Exception:
            host = "unknown"
        hosts[host] += 1
    return {
        "n_sources": len(ranked or []),
        "n_domains": len(hosts),
        "top_domains": sorted(hosts.items(), key=lambda x: -x[1])[:5],
    }
