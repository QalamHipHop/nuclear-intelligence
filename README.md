# ⚛️ Nuclear Intelligence v2.0

**AI-Powered Nuclear Energy Research & NES Token System**

> ✅ **Upgraded with FREE LLM providers** — Groq, Together AI, Cloudflare Workers AI, OpenRouter, HuggingFace. No OpenAI API needed!

---

## ✨ What's New in v2.0

- ✅ **Free LLM Providers**: Groq (fastest LPU) → Together AI → Cloudflare → OpenRouter → HuggingFace
- ✅ **Auto-Fallback Chain**: Switches providers automatically when one fails
- ✅ **Developer Mode**: Advanced chain-of-thought analysis, cross-domain insights
- ✅ **Enhanced Security**: HMAC signatures, Merkle tree verification, POW mining
- ✅ **Real-time Dashboard**: Live stats, accuracy/novelty charts, LLM provider health
- ✅ **Web Search**: DuckDuckGo integration for fresh research
- ✅ **Rate-Limited API**: FastAPI with security middleware
- ✅ **Comprehensive Export**: JSON + Markdown knowledge exports

---

## 🚀 Quick Start

```bash
git clone https://github.com/QalamHipHop/nuclear-intelligence.git
cd nuclear-intelligence
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/initialize_knowledge_base.py

# Add at least one API key to .env, then:
python app.py  # Opens at http://localhost:7860
```

---

## 🔑 Free API Keys (Get at least ONE)

| Provider | Speed | Free Tier | Link |
|----------|-------|-----------|------|
| **Groq** ⭐ | ⚡⚡⚡ | 60 req/min | console.groq.com |
| **Together AI** | ⚡⚡ | 30 req/min | api.together.xyz |
| **Cloudflare** | ⚡⚡ | 1000/day | dash.cloudflare.com |
| **OpenRouter** | ⚡ | Free credits | openrouter.ai |
| **HuggingFace** | ⚡ | Rate limited | huggingface.co/settings/tokens |

Your HF token is already configured: `hf_YOUR_TOKEN_HERE`

---

## 🏗️ Architecture

```
Nuclear Intelligence v2.0
├── core/
│   ├── llm_engine.py      # Multi-provider LLM (Groq/Together/Cloudflare/OpenRouter/HF)
│   ├── nuclear_intelligence.py  # RAG + evaluation engine
│   ├── operation_loop.py  # Autonomous research-to-tokenization
│   ├── knowledge_graph.py # Advanced KG with export
│   ├── embeddings.py     # Local sentence-transformers (free)
│   └── web_search.py      # DuckDuckGo (free)
├── blockchain/
│   └── virtual_ledger.py  # POW + Merkle + NES minting
├── api/
│   └── main.py           # FastAPI with rate limiting
├── app.py                # Gradio UI dashboard
└── scripts/
    ├── initialize_knowledge_base.py
    └── sync_huggingface.py
```

---

## 🔄 Operation Cycle

```
Question → RAG + Web Search → Research → Evaluation → Quality Gate
                                                    ↓
                                         ✅ Pass → Mint NES Token
                                         ❌ Fail → Reject & Log
```

Quality thresholds: Accuracy ≥93%, Novelty ≥70%, Usefulness ≥75%

---

## 🪙 NES Token System

- **1 NES token** per validated scientific advancement
- Proof-of-work mining with configurable difficulty
- Merkle tree transaction verification
- HMAC cryptographic signatures
- Immutable blockchain ledger

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | System status + LLM provider |
| POST | `/api/v1/knowledge/ask` | Ask a nuclear question |
| GET | `/api/v1/knowledge/base` | Knowledge graph |
| POST | `/api/v1/operations/cycle` | Trigger research cycle |
| GET | `/api/v1/blockchain/state` | Blockchain stats |
| GET | `/api/v1/blockchain/verify` | Chain integrity |
| GET | `/api/v1/developer/system-diag` | Full diagnostics |
| GET | `/api/v1/developer/export-all` | Export all data |

Full docs: `http://localhost:8000/docs`

---

## 🐳 Docker

```bash
docker build -t nuclear-intelligence .
docker run -p 7860:7860 -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e HF_TOKEN=hf_your_token \
  nuclear-intelligence
```

---

## 🔐 Security

- HMAC transaction signatures
- Merkle tree proof verification  
- Rate limiting (configurable per endpoint)
- CORS middleware
- Request logging
- Chain integrity verification

---

**MIT License — Qalam | Powered by free LLM providers**
