# Nuclear Intelligence System v2.0

Advanced AI-powered autonomous nuclear energy research and knowledge tokenization system with blockchain integration and NES stablecoin backing.

## 🎯 Project Overview

**Nuclear Intelligence** is an autonomous system designed to:

1. **Generate Complex Questions** about nuclear energy spanning physics, engineering, economics, safety, and novel applications
2. **Conduct Deep Research** using advanced RAG, external sources (arXiv, web), and knowledge graphs
3. **Evaluate Answers** using multi-layer criteria (scientific accuracy ≥93%, novelty, usefulness, self-consistency)
4. **Mint NES Tokens** for validated knowledge on an immutable blockchain
5. **Operate Continuously** with 24/7 uptime and autonomous execution

## 🏗️ System Architecture

### Core Components

#### 1. Nuclear Intelligence Core (NI Core)
- **Advanced RAG System:** Vector database (FAISS), hybrid search, reranking
- **Knowledge Graph:** Structured knowledge representation and retrieval
- **External Research Tools:** arXiv integration, web search capabilities
- **Multi-layer Evaluation:** Scientific accuracy, novelty, usefulness, self-consistency

#### 2. Enhanced Virtual Ledger (Blockchain)
- **Full Blockchain Features:** SHA-256 hashing, Merkle trees, digital signatures
- **NES Token Minting:** 1 token per validated scientific advancement
- **External Network Sync:** Mirroring with external blockchain networks
- **Transaction Management:** Comprehensive history and state tracking

#### 3. Operation Loop
- **Autonomous Execution:** Runs every 30-60 minutes
- **5-Step Process:**
  1. Generate 1-3 complex questions
  2. Conduct deep research
  3. Multi-layer evaluation
  4. Token minting (if approved)
  5. Knowledge integration
- **Error Recovery:** Intelligent fallback mechanisms

#### 4. FastAPI Backend
- **RESTful API:** Comprehensive endpoints for all operations
- **Real-time Monitoring:** System status, statistics, blockchain state
- **External Integration:** Webhook support for external blockchain networks

#### 5. Gradio UI
- **Dashboard:** System statistics and monitoring
- **Research Cycle:** Execute and monitor research cycles
- **Blockchain Explorer:** View knowledge records and minting queue
- **Configuration:** System settings and thresholds

## 📋 Requirements

### System Requirements
- Python 3.8+
- 8GB RAM minimum (16GB recommended)
- GPU support (NVIDIA CUDA) for optimal performance

### Dependencies
See `requirements_enhanced.txt` for complete list. Key packages:
- FastAPI, Uvicorn (API server)
- Gradio (UI)
- OpenAI, LangChain (LLM integration)
- FAISS, Sentence-Transformers (Vector database)
- Torch, Transformers (ML models)
- arXiv, BeautifulSoup (Research tools)

## 🚀 Installation and Setup

### 1. Clone Repository
```bash
git clone https://github.com/QalamHipHop/nuclear-intelligence.git
cd nuclear-intelligence
```

### 2. Install Dependencies
```bash
pip install -r requirements_enhanced.txt
```

### 3. Configure Environment
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

### 4. Initialize Knowledge Base
```bash
python scripts/initialize_knowledge_base.py
```

## 🔧 Configuration

Edit `.env` file with the following key settings:

```env
# LLM Configuration
OPENAI_API_KEY=your-api-key
LLM_MODEL=gpt-4-turbo

# Hugging Face
HUGGINGFACE_API_KEY=your-token

# Evaluation Thresholds
SCIENTIFIC_ACCURACY_THRESHOLD=93
NOVELTY_THRESHOLD=75
USEFULNESS_THRESHOLD=80
SELF_CONSISTENCY_THRESHOLD=90
OVERALL_SCORE_THRESHOLD=85

# Operation Loop
OPERATION_LOOP_INTERVAL_MINUTES=30
QUESTIONS_PER_CYCLE=3
```

## ▶️ Running the System

### Option 1: Gradio UI (Recommended for Development)
```bash
python app_enhanced.py
# Access at http://localhost:7860
```

### Option 2: FastAPI Backend
```bash
python -m uvicorn api.enhanced_api:app --host 0.0.0.0 --port 8000
# API documentation at http://localhost:8000/docs
```

### Option 3: Continuous Operation Loop
```bash
python -c "
import asyncio
from core.enhanced_operation_loop import EnhancedOperationLoop

config = {
    'llm_model': 'gpt-4-turbo',
    'openai_api_key': 'your-key',
    # ... other config
}

loop = EnhancedOperationLoop(config)
asyncio.run(loop.run_continuous_loop(interval_minutes=30))
"
```

## 📊 API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - System status
- `GET /api/v2/statistics/operations` - Operation statistics

### Research
- `POST /api/v2/research/questions` - Generate questions
- `POST /api/v2/research/cycle` - Execute research cycle

### Blockchain
- `GET /api/v2/blockchain/state` - Blockchain state
- `GET /api/v2/blockchain/knowledge-records` - Knowledge records
- `GET /api/v2/blockchain/export` - Export ledger
- `GET /api/v2/blockchain/balance/{address}` - NES balance

### External Integration
- `GET /api/v2/external/minting-queue` - Minting queue
- `POST /api/v2/external/process-minting` - Process external minting

### Knowledge Base
- `GET /api/v2/knowledge/summary` - Knowledge summary

## 🔐 Security Considerations

1. **API Keys:** Store securely in `.env`, never commit to repository
2. **Blockchain Secret:** Use strong, unique secret for transaction signing
3. **External Network:** Verify RPC endpoints and contract addresses
4. **Rate Limiting:** Implement rate limiting for production deployment
5. **Input Validation:** All inputs are validated using Pydantic models

## 📈 Monitoring and Logging

- **Logs:** Check `logs/nuclear_intelligence.log` for detailed logs
- **Dashboard:** Access Gradio UI for real-time monitoring
- **API Endpoints:** Use `/status` endpoint for programmatic monitoring
- **Blockchain Explorer:** View all transactions and knowledge records

## 🚀 Deployment

### Hugging Face Spaces
1. Create new Space with Gradio template
2. Connect GitHub repository
3. Set environment variables in Space settings
4. Enable "Always-On" for continuous operation

### Docker
```bash
docker build -t nuclear-intelligence .
docker run -p 7860:7860 -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  nuclear-intelligence
```

### GitHub Actions (Keep-Alive)
```yaml
name: Keep Alive
on:
  schedule:
    - cron: '*/25 * * * *'
jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Hugging Face Space
        run: curl https://huggingface.co/spaces/Qalam/Nuclear-Intelligence
```

## 📚 Project Structure

```
nuclear-intelligence/
├── core/
│   ├── nuclear_intelligence_enhanced.py    # NI Core
│   ├── enhanced_operation_loop.py           # Operation Loop
│   └── __init__.py
├── blockchain/
│   ├── enhanced_virtual_ledger.py          # Virtual Ledger
│   └── __init__.py
├── api/
│   ├── enhanced_api.py                     # FastAPI Backend
│   └── __init__.py
├── scripts/
│   ├── initialize_knowledge_base.py
│   ├── run_operation_cycle.py
│   └── sync_huggingface.py
├── knowledge_base/
│   ├── nuclear_knowledge_base.json
│   └── knowledge_index.json
├── app_enhanced.py                         # Gradio UI
├── requirements_enhanced.txt               # Dependencies
├── .env.template                           # Configuration template
├── README_ENHANCED.md                      # This file
└── Dockerfile                              # Docker configuration
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is open-source. See LICENSE file for details.

## 🔗 Links

- **GitHub:** https://github.com/QalamHipHop/nuclear-intelligence
- **Hugging Face:** https://huggingface.co/spaces/Qalam/Nuclear-Intelligence
- **Documentation:** See ARCHITECTURE.md for detailed technical documentation

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Developed by:** Qalam Hip Hop  
**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** 2026-06-09
