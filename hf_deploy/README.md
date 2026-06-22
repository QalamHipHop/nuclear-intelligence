---
title: Nuclear Intelligence
emoji: ⚛️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
python_version: 3.11
app_file: app.py
pinned: false
license: mit
tags:
  - nuclear
  - energy
  - AI
  - research
  - blockchain
  - knowledge-graph
  - LLM
  - free-models
  - deepseek
  - groq
  - fusion
---

# Nuclear Intelligence v4.0 ⚛️

**AI-Powered Nuclear Energy Research & NES Token System**

![Nuclear Intelligence](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Features

- **🤖 7 Free LLM Providers** with intelligent fallback — DeepSeek, Groq, Gemini, Together, Fireworks, AIMLAPI, HuggingFace
- **🔬 AI Research Engine** — automated nuclear energy research with multi-dimensional evaluation
- **⛓️ Virtual Blockchain** — POW mining with adaptive difficulty, NES token minting
- **🕸️ Knowledge Graph** — entity relationships, advanced search, analytics
- **🛡️ Safety Guardrails** — defensive filter for weapons / proliferation / RDD queries (v4.0)
- **📊 Real-time Monitoring** — live stats, health checks, visualization dashboards
- **🌐 Multilingual** — automatic Persian / English detection
- **🔬 Developer Mode** — deep cross-domain analysis, research gap identification

## 🚀 Quick Start

1. **Add API Keys** in the Space's *Settings → Variables and secrets* (optional — demo mode works without keys):
   ```
   AIMLAPI_API_KEY=...
   DEEPSEEK_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   GEMINI_API_KEY=...
   HF_TOKEN=hf_...
   TOGETHER_API_KEY=...
   FIREWORKS_API_KEY=...
   ```
2. **The app auto-detects available providers and falls back gracefully**
3. **Run Research Cycles** or **Ask Questions** about nuclear energy
4. Try the **🛡️ Safety & Health** tab for prompt-policy self-tests

## 📋 Requirements

All dependencies are pre-installed. Main packages:
- `gradio>=4.36.0` — UI framework
- `openai>=1.12.0` — LLM API calls
- `loguru>=0.7.2` — logging
- `pandas>=2.2.0` — data analysis
- `plotly>=5.19.0` — visualization
- `requests` — web search

## 🏗️ Architecture

```
Nuclear Intelligence v4.0
├── LLM Engine          — 7-provider multi-model routing with fallback
├── Research Core       — RAG + multi-layer evaluation pipeline
├── Knowledge Graph     — entity management & semantic search
├── Blockchain          — POW mining + NES tokens
├── Safety Guard        — weapons / proliferation / RDD filter (v4.0)
├── Enhanced Eval       — self-consistency + citation quality + readiness
├── Enhanced RAG        — domain-weighted re-ranking + diversity
├── i18n                — Persian / English detection
└── Gradio UI           — 6-tab real-time dashboard
```

## 🪙 NES Token System

Research cycles evaluate answers on five dimensions:

| Dimension | Weight |
|---|---|
| Scientific Accuracy | 45 % |
| Novelty Score | 25 % |
| Usefulness | 20 % |
| Completeness | 10 % |
| *(v4.0)* Self-Consistency + Citation Quality | tiebreaker |

Answers scoring **≥ 82 %** overall are minted as NES tokens and recorded on the virtual blockchain.

## 📊 Quality Thresholds (v4.0)

| Metric | Threshold |
|---|---|
| Scientific Accuracy | ≥ 93 % |
| Novelty Score | ≥ 75 % |
| Usefulness | ≥ 80 % |
| Self-Consistency | ≥ 0.80 |
| Citation Quality | ≥ 50 |
| **Overall (Tokenization-Readiness)** | **≥ 85 %** |

## 🔧 Configuration

Add to `.env` file or Space variables:
```env
DEVELOPER_MODE=true
AUTO_START_LOOP=false
SCIENTIFIC_ACCURACY_THRESHOLD=93
MIN_NOVELTY_THRESHOLD=75
MIN_USEFULNESS_THRESHOLD=80
MIN_OVERALL_SCORE=85
OPERATION_LOOP_INTERVAL_MINUTES=30
```

## 🛡️ Safety Policy (v4.0)

The Space enforces a *defensive* policy on every user prompt:

- Refuses weapons design, illicit enrichment, weapons-usable material handling
- Refuses radiological dispersal device ("dirty bomb") instructions
- Refuses cyber-proliferation guidance for nuclear facilities
- Refuses illicit-trafficking assistance
- **Redirects** refused prompts to the legitimate peaceful-use side of the topic

Compliance: NPT, IAEA safeguards, NSG / Zangger Committee, PSI.

## 🩺 Health Check

Run anytime (also available in the Gradio UI):
```bash
python scripts/health_check.py
```

## 📜 License

MIT License — © QalamHipHop

## 🔗 Links

- [GitHub](https://github.com/QalamHipHop/nuclear-intelligence)
- [HuggingFace Space](https://huggingface.co/spaces/Qalam/Nuclear-Intelligence)
- [CHANGELOG v4.0](https://github.com/QalamHipHop/nuclear-intelligence/blob/main/CHANGELOG_V4.md)

---

**Built with ❤️ for the safe advancement of nuclear energy.**
