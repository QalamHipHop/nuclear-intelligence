# ⚛️ Nuclear Intelligence v4.0

**AI-Powered Nuclear Energy Research & NES Token System**

> ✅ **Fully upgraded with FREE LLM providers** — DeepSeek V3, Groq, Cerebras, Gemini 2.0, Fireworks, Together AI, OpenRouter, HuggingFace. **No OpenAI API needed!**

[![HuggingFace Spaces](https://img.shields.io/badge/HuggingFace-Space-blue)](https://huggingface.co/spaces/Qalam/Nuclear-Intelligence)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ What's New in v4.0

- 🚀 **10 Free LLM Providers**: DeepSeek V3 → Groq → Cerebras → Gemini → Fireworks → Together → Novita → OpenRouter → Cloudflare → HuggingFace
- 🧠 **Intelligent Routing**: Auto-fallback with caching, rate limiting, and health monitoring
- 📊 **Enhanced Evaluation**: Multi-dimensional scoring (accuracy, novelty, usefulness, completeness)
- 🔬 **Developer Mode**: Deep cross-domain analysis, research gap detection, confidence scoring
- ⛓️ **Advanced Blockchain**: POW mining, Merkle trees, HMAC signatures, adaptive difficulty
- 🎨 **Beautiful UI**: Real-time stats, charts, searchable knowledge graph
- 💾 **Multiple Exports**: JSON, Markdown, CSV
- 🔐 **Security**: Rate limiting, input sanitization, HMAC signatures

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/QalamHipHop/nuclear-intelligence.git
cd nuclear-intelligence

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.template .env
# Edit .env and add your free API keys

# Run the application
python app.py
```

### Docker

```bash
docker-compose up -d
```

---

## 🔑 Free API Keys Setup

**All providers below are 100% FREE — no credit card needed!**

| Provider | Speed | Model | Free Tier | Link |
|----------|-------|-------|-----------|------|
| **DeepSeek V3** | ⭐⭐⭐ | DeepSeek V3 (128K ctx) | Yes | [console.deepseek.com](https://console.deepseek.com) |
| **Groq** | ⭐⭐⭐ | Llama 3.3 70B | Yes | [console.groq.com](https://console.groq.com) |
| **Cerebras** | ⭐⭐⭐ | Llama 3.3 70B | Yes | [cloud.cerebras.ai](https://cloud.cerebras.ai) |
| **Gemini 2.0** | ⭐⭐ | Gemini 2.0 Flash | Yes | [aistudio.google.com](https://aistudio.google.com) |
| **Fireworks** | ⭐⭐ | DeepSeek V3 | Yes | [fireworks.ai](https://fireworks.ai) |
| **Together AI** | ⭐⭐ | Llama 3.3 70B | Credits | [api.together.xyz](https://api.together.xyz) |
| **Novita AI** | ⭐⭐ | DeepSeek V3 (128K) | Yes | [novita.ai](https://novita.ai) |
| **OpenRouter** | ⭐ | Multiple free | Daily free | [openrouter.ai](https://openrouter.ai) |
| **Cloudflare** | ⭐ | Llama 3.1 8B | 1000/day | [dash.cloudflare.com](https://dash.cloudflare.com) |
| **HuggingFace** | ⭐ | Qwen 72B | Your token | ✅ Already configured |

Add these to your `.env` file:

```bash
DEEPSEEK_API_KEY=sk-your_key
GROQ_API_KEY=gsk_your_key
GEMINI_API_KEY=your_key
FIREWORKS_API_KEY=fw_your_key
CEREBRAS_API_KEY=cb_your_key
# etc.
```

---

## 🏗️ Architecture

```
Nuclear Intelligence v4.0
├── app.py                   # Gradio UI Dashboard
├── api/main.py              # FastAPI REST API (30+ endpoints)
├── core/
│   ├── llm_engine.py        # 10-provider LLM engine with caching
│   ├── nuclear_intelligence.py  # RAG + multi-dimension evaluation
│   ├── operation_loop.py    # Autonomous research-to-tokenization
│   ├── knowledge_graph.py   # Advanced graph with search & analytics
│   ├── embeddings.py        # Local sentence-transformers (free)
│   └── web_search.py        # DuckDuckGo (free)
├── blockchain/
│   └── virtual_ledger.py    # POW + Merkle + adaptive difficulty
└── scripts/
    ├── sync_huggingface.py  # Auto-sync to HF dataset
    └── verify_blockchain.py # Chain verification
```

---

## 🎯 Features

### Research Engine
- **Multi-provider LLM**: Automatic fallback through 10 free providers
- **RAG Pipeline**: Local FAISS vector store with sentence-transformers embeddings
- **Web Search**: DuckDuckGo integration for real-time research
- **Multi-dimensional Evaluation**: Scientific accuracy, novelty, usefulness, completeness

### NES Token System
- **Proof-of-Work Mining**: Adaptive difficulty blockchain
- **Merkle Tree Verification**: Cryptographic transaction verification
- **HMAC Signatures**: SHA3-512 cryptographic signatures
- **Auto-minting**: Research cycles that pass thresholds automatically mint tokens

### Knowledge Graph
- **Entity Management**: Research questions stored as graph entities
- **Advanced Search**: Full-text search with relevance scoring
- **Category Analytics**: Distribution charts and statistics
- **Multiple Exports**: JSON, Markdown, CSV formats

### Developer Mode
- **Physics Depth Analysis**: Deep technical analysis
- **Cross-Domain Connections**: Links between nuclear subfields
- **Research Gap Detection**: Identifies areas needing further study
- **Confidence Scoring**: Self-assessment of research quality

---

## 📡 API Endpoints

### Knowledge
- `POST /api/v1/knowledge/ask` - Ask a nuclear energy question
- `GET /api/v1/knowledge/search` - Search knowledge graph
- `GET /api/v1/knowledge/categories` - Get category stats

### Blockchain
- `GET /api/v1/blockchain/state` - Get blockchain state
- `GET /api/v1/blockchain/verify` - Verify chain integrity
- `GET /api/v1/blockchain/transactions` - Get transaction history

### Operations
- `POST /api/v1/operations/cycle` - Trigger manual research cycle
- `POST /api/v1/operations/start` - Start autonomous loop
- `GET /api/v1/operations/stats` - Get loop statistics

### Developer
- `GET /api/v1/developer/llm-status` - LLM provider health
- `GET /api/v1/developer/system-diag` - Full system diagnostics
- `GET /api/v1/developer/export-all` - Export all data

Full API docs at: `http://localhost:8000/docs`

---

## ⚙️ Configuration

### Quality Thresholds
```bash
SCIENTIFIC_ACCURACY_THRESHOLD=93  # Min accuracy to mint
MIN_NOVELTY_THRESHOLD=70          # Min novelty score
MIN_USEFULNESS_THRESHOLD=75       # Min usefulness score
MIN_OVERALL_SCORE=82              # Min weighted overall score
```

### Operation Loop
```bash
AUTO_START_LOOP=true              # Start loop on startup
OPERATION_LOOP_INTERVAL_MINUTES=30 # Minutes between cycles
DEVELOPER_MODE=true               # Enable developer analysis
```

---

## 🐳 Docker Deployment

```yaml
# docker-compose.yml
services:
  nuclear-intelligence:
    build: .
    ports:
      - "7860:7860"  # Gradio UI
      - "8000:8000"  # FastAPI
    environment:
      - HF_TOKEN=${HF_TOKEN}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - DEVELOPER_MODE=true
    volumes:
      - ./knowledge_base:/app/knowledge_base
      - ./reports:/app/reports
```

---

## 🔒 Security

- **HMAC-SHA3-512** signatures on all transactions
- **Merkle tree** verification for block integrity
- **Per-provider rate limiting** (sliding window)
- **Input sanitization** for all user queries
- **Adaptive POW difficulty** based on mining speed

---

## 📊 Token Economics

NES tokens are minted when research passes quality thresholds:

| Score | Weight | Threshold |
|-------|--------|-----------|
| Scientific Accuracy | 45% | ≥93% |
| Novelty | 25% | ≥70% |
| Usefulness | 20% | ≥75% |
| Completeness | 10% | ≥50% |
| **Overall** | **100%** | **≥82%** |

Tokens are tracked on the virtual blockchain with full transaction history.

---

## 🌐 HuggingFace Space

The project runs on HuggingFace Spaces at:
**https://huggingface.co/spaces/Qalam/Nuclear-Intelligence**

- Auto-deploys from GitHub on push
- Uses HF token for Inference API
- Zero infrastructure cost with free tier

---

## 📝 License

MIT License - Qalam | Powered by free LLM providers

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add free LLM providers or features
4. Submit a pull request

---

*Built with ❤️ using DeepSeek, Groq, Cerebras, Gemini, and HuggingFace - all free, no OpenAI needed.*