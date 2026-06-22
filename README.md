---
title: Nuclear Intelligence
emoji: ⚛️
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 4.36.0
python_version: 3.11
app_file: app.py
pinned: false
---

# ⚛️ Nuclear Intelligence v4.0

> Autonomous nuclear-energy research pipeline that turns validated Q&A into on-chain NES tokens.

**Nuclear Intelligence** is a 24/7 autonomous system that:

1. **Generates** cutting-edge research questions about nuclear energy (fusion, SMR, Gen IV, waste, materials, safety, AI-assisted design, etc.)
2. **Researches** each question using a chain of free LLM providers (HF Router, Groq, DeepSeek, Gemini, Together, Fireworks, AIMLAPI) with automatic fallback.
3. **Evaluates** every answer with an independent LLM call (multi-layer: accuracy, novelty, usefulness, completeness, self-consistency).
4. **Mints** a NES token on a real SHA-3 Proof-of-Work blockchain for every answer that passes the thresholds.
5. **Syncs** all minted records to a public HuggingFace Dataset *and* the GitHub repo, so the corpus is openly readable.

## 🛡️ v4.0 Highlights (June 2026)

- **Safety & Ethics Guardrails** — hard pre-LLM + post-generation filter; refuses weapons / proliferation / RDD / cyber-proliferation prompts and redirects to legitimate peaceful-use topics.
- **Enhanced Evaluation** — multi-pass self-consistency, citation-quality scoring, novelty vs Knowledge Graph, and a Tokenization-Readiness composite (Accuracy ≥ 93 %, Novelty ≥ 75 %, Usefulness ≥ 80 %, Overall ≥ 85 %).
- **Enhanced RAG** — domain weighting (IAEA 2.5×, NRC 2.5×, peer-reviewed 1.7–1.8×), recency boost, diversity round-robin.
- **Multilingual** — automatic Persian / English detection + localized UI labels.
- **Security** — hardcoded API keys removed from `app.py` and LLM engines; all keys now flow through `.env` only.
- **Health Check** — `python scripts/health_check.py` runs 9 smoke tests; available in the Gradio UI under **🛡️ Safety & Health**.

See [CHANGELOG_V4.md](CHANGELOG_V4.md) for the full release notes.

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────┐
                    │  GitHub Actions (every 25m)  │
                    │  • run_operation_cycle.py    │
                    │  • sync_huggingface.py       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
            ┌──────────────────────────────────────────┐
            │  NuclearIntelligenceCore (core/)         │
            │  ┌────────┐  ┌────────┐  ┌────────────┐  │
            │  │ LLM    │  │ RAG    │  │ Knowledge  │  │
            │  │ Engine │  │ FAISS  │  │ Graph      │  │
            │  └────┬───┘  └────────┘  └────────────┘  │
            │       │ multi-provider fallback         │
            └───────┼──────────────────────────────────┘
                    ▼
            ┌──────────────────┐    ┌──────────────────┐
            │ VirtualLedger    │    │ HF Dataset       │
            │ SHA-3 PoW chain  │◄──►│ (public)         │
            │ NES tokens       │    │ + GitHub repo    │
            └──────────────────┘    └──────────────────┘
```

**Two deployment modes:**
- **GitHub Actions** (`.github/workflows/operation-loop.yml`) — runs the full pipeline every 25 min.
- **HuggingFace Space** (`hf_deploy/app.py`) — Gradio UI + the same pipeline, runs 24/7 if upgraded to a paid tier, otherwise kept alive by `keep_alive.yml`.

---

## 🚀 Quick Start

### HuggingFace Space (easiest)
1. Visit https://huggingface.co/spaces/Qalam/Nuclear-Intelligence
2. Click **Run Research Cycle** to mint a token.
3. Browse the **Blockchain** and **Knowledge Graph** tabs.

### GitHub Actions (production)
1. Fork this repo.
2. Add secrets in **Settings → Secrets and variables → Actions**:
   - `HF_TOKEN` (required)
   - `GITHUB_TOKEN` (auto-provided, but `secrets.GITHUB_TOKEN` is read-only for PRs — use a PAT if you need to push from PRs)
   - `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, etc. (optional, for more LLM providers)
3. The workflow runs every 25 minutes automatically.

### Local development
```bash
git clone https://github.com/QalamHipHop/nuclear-intelligence.git
cd nuclear-intelligence
pip install -r requirements.txt
cp .env.template .env  # fill in API keys
python scripts/run_operation_cycle.py  # one cycle
python -m uvicorn api.health:app --reload  # API on :8000
```

---

## 🔑 Required Secrets

| Secret | Required? | Used by |
|---|---|---|
| `HF_TOKEN` | ✅ | LLM provider, dataset sync, space deploy |
| `GITHUB_TOKEN` | optional | report commit, ledger push |
| `GROQ_API_KEY` | optional | LLM provider (fastest) |
| `DEEPSEEK_API_KEY` | optional | LLM provider (best free) |
| `GEMINI_API_KEY` | optional | LLM provider |
| `TOGETHER_API_KEY` | optional | LLM provider |
| `FIREWORKS_API_KEY` | optional | LLM provider |
| `AIMLAPI_API_KEY` | optional | LLM provider |
| `BLOCKCHAIN_SECRET` | optional | HMAC for tx signing |

Without any LLM key, the system falls back to **demo mode** (no real research, no minting).

---

## 📁 Project Structure

```
nuclear-intelligence/
├── core/                         # Main pipeline (LLM + RAG + KG)
│   ├── llm_engine_v4.py         # Multi-provider LLM engine
│   ├── nuclear_intelligence_v4.py  # Research-to-token pipeline
│   ├── operation_loop_v4.py     # Autonomous loop
│   ├── knowledge_graph.py       # KG
│   ├── embeddings.py            # Sentence-transformers wrapper
│   └── web_search.py            # arXiv / web research
├── blockchain/
│   └── virtual_ledger.py        # SHA-3 PoW blockchain
├── api/
│   ├── health.py                # Health check + cycle trigger API
│   ├── main.py                  # Legacy FastAPI
│   └── enhanced_api.py          # Full FastAPI
├── hf_deploy/                    # Self-contained for HF Space
│   ├── app.py                   # Gradio UI + inline pipeline
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/
│   ├── run_operation_cycle.py   # One cycle entrypoint
│   ├── sync_huggingface.py      # Push to HF dataset + GH
│   ├── initialize_knowledge_base.py
│   └── keep_alive.py
├── knowledge_base/              # Persisted state (gitignored)
├── reports/                     # Cycle reports (gitignored)
├── logs/                        # Runtime logs (gitignored)
├── .github/workflows/
│   ├── operation-loop.yml       # Every 25 min
│   ├── keep_alive.yml           # Every 20 min (ping HF Space)
│   ├── deploy-hf.yml            # Push hf_deploy → Space
│   └── ci-cd.yml                # Lint + smoke tests
├── requirements.txt
├── requirements_enhanced.txt
├── requirements_hf.txt
└── docker-compose.yml
```

---

## ⚙️ Configuration

Edit `.env` (or set GitHub Actions secrets):

```env
# Mint thresholds
MIN_ACCURACY=70
MIN_NOVELTY=60
MIN_USEFULNESS=60
MIN_OVERALL=65

# Mining
POW_DIFFICULTY=3        # 3 ≈ a few seconds; 4 ≈ a minute; 5+ = slow

# Loop
OPERATION_LOOP_INTERVAL_MINUTES=25

# LLM
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=4096
```

---

## 📊 API

Run locally: `uvicorn api.health:app --port 8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (checks LLM configured) |
| GET | `/stats` | Full system stats |
| GET | `/chain` | Blockchain stats |
| GET | `/recent?limit=20` | Recent cycles |
| GET | `/search?q=...` | Search knowledge graph |
| POST | `/cycle` | Trigger a research cycle |
| POST | `/cycle` with `{"question": "..."}` | Direct Q&A |

Full docs at `/docs` (Swagger UI).

---

## 🪙 NES Tokenomics

- **Symbol:** NES (Nuclear Energy Science)
- **Mint rate:** 1 NES per validated research cycle (when all 4 thresholds + consistency pass)
- **Supply:** unbounded but rate-limited by the 25-min loop
- **Ledger:** `/knowledge_base/virtual_ledger.json` (full chain with PoW)
- **Public mirror:** https://huggingface.co/datasets/Qalam/nuclear-intelligence-dataset

The chain is a real blockchain:
- SHA-3-256 block hashes
- Real Proof-of-Work (configurable difficulty)
- Adaptive difficulty (raises if blocks mined too fast, lowers if too slow)
- Merkle-tree transaction verification
- HMAC-signed transactions

---

## 🧪 Testing

```bash
# Quick import + smoke test
python -c "from core.nuclear_intelligence import NuclearIntelligenceCore; print('OK')"

# Full ledger test
python -c "
from blockchain.virtual_ledger import VirtualLedger
import tempfile, os
with tempfile.TemporaryDirectory() as tmp:
    ledger = VirtualLedger(ledger_file=os.path.join(tmp, 'l.json'), difficulty=1)
    assert ledger.is_valid()
    ledger.mint({'test': True})
    assert ledger.is_valid()
    assert ledger.nes_supply == 1.0
    print('✅ ledger OK')
"

# GitHub Actions also runs these in .github/workflows/ci-cd.yml
```

---

## 🤝 Contributing

1. Fork the repo.
2. Create a feature branch.
3. Run `python -m pytest tests/` (if you add tests).
4. Open a pull request.

The CI will run lint + smoke tests automatically.

---

## 📜 License

MIT

---

## 🔗 Links

- **GitHub:** https://github.com/QalamHipHop/nuclear-intelligence
- **HuggingFace Space:** https://huggingface.co/spaces/Qalam/Nuclear-Intelligence
- **HuggingFace Dataset:** https://huggingface.co/datasets/Qalam/nuclear-intelligence-dataset
- **Architecture docs:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
