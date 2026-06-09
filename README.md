---
title: Nuclear Intelligence
emoji: ⚛️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Nuclear Intelligence 🧬⚛️

**AI-Powered Nuclear Energy Research & Blockchain-Based NES Token System**

A sophisticated system that combines advanced AI, Retrieval-Augmented Generation (RAG), and blockchain technology to accelerate nuclear energy knowledge creation and economic tokenization through the NES token.

---

## 🎯 Project Vision

**Nuclear Intelligence** transforms scientific breakthroughs in nuclear energy into economic value through:

1. **Automated Research**: AI-powered generation of complex, multidimensional research questions
2. **Deep Knowledge Synthesis**: RAG-enhanced research combining academic papers, web data, and domain knowledge
3. **Multi-Layer Evaluation**: Professional assessment of scientific accuracy, novelty, and usefulness
4. **Knowledge Tokenization**: Minting of NES tokens for validated scientific contributions
5. **Immutable Ledger**: Virtual blockchain ensuring transparency and auditability

---

## 🏗️ System Architecture

### Core Components

#### 1. **Nuclear Intelligence Core** (`core/nuclear_intelligence.py`)
- Advanced LLM integration (GPT-4 Turbo, Qwen, Llama)
- RAG system with FAISS vector database
- Knowledge Graph management
- Multi-layer evaluation engine
- ArXiv integration for academic research

#### 2. **Virtual Blockchain Ledger** (`blockchain/virtual_ledger.py`)
- Immutable transaction recording
- Proof-of-work block mining
- NES token minting mechanism
- Complete blockchain state management
- Merkle tree construction

#### 3. **Operation Loop** (`core/operation_loop.py`)
- Automated research-to-tokenization pipeline
- Configurable execution intervals
- Comprehensive cycle reporting
- Statistics tracking and analysis

#### 4. **FastAPI Application** (`api/main.py`)
- RESTful API for system interaction
- Knowledge base queries
- Blockchain state endpoints
- System management and monitoring

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Hugging Face token
- GitHub token (for CI/CD)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/QalamHipHop/nuclear-intelligence.git
cd nuclear-intelligence
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.template .env
# Edit .env with your credentials
```

5. **Initialize knowledge base**
```bash
python scripts/initialize_knowledge_base.py
```

### Running the System

#### Option 1: API Server
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Access API documentation at `http://localhost:8000/docs`

#### Option 2: Single Operation Cycle
```bash
python scripts/run_operation_cycle.py
```

#### Option 3: Docker (for Hugging Face Space)
```bash
docker build -t nuclear-intelligence .
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN nuclear-intelligence
```

---

## 📊 Operation Cycle

Each cycle executes the following pipeline:

### Step 1: Question Generation
- Creates 1-3 complex, multidimensional research questions
- Combines physics, engineering, economics, safety, applications, and AI
- Assigns complexity levels and keywords

### Step 2: Deep Research
- Retrieves relevant documents from vector database
- Searches ArXiv for recent papers
- Performs web searches for current information
- Synthesizes comprehensive answers with equations and examples

### Step 3: Multi-Layer Evaluation
- **Scientific Accuracy** (≥93% threshold)
- **Novelty Score** (semantic comparison with knowledge base)
- **Usefulness Score** (for NES valuation and innovation)
- **Self-Consistency** (multiple validation tests)

### Step 4: Token Minting
- Creates immutable record in virtual blockchain
- Mints 1 NES token per approved answer
- Records complete metadata and citations
- Updates ledger with transaction

### Step 5: Knowledge Base Update
- Adds validated answer to knowledge base
- Updates vector database with new embeddings
- Triggers optional LoRA fine-tuning
- Uploads dataset to Hugging Face

### Step 6: Block Mining
- Mines new block with all pending transactions
- Verifies blockchain integrity
- Exports ledger state

---

## 🔗 API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - System status
- `GET /api/v1/system/config` - System configuration

### Knowledge Management
- `POST /api/v1/knowledge/ask` - Ask a question
- `GET /api/v1/knowledge/base` - Get knowledge base
- `GET /api/v1/knowledge/records` - Get knowledge records

### Blockchain
- `GET /api/v1/blockchain/state` - Blockchain state
- `GET /api/v1/blockchain/chain` - Complete blockchain
- `GET /api/v1/blockchain/balance/{address}` - NES balance
- `GET /api/v1/blockchain/transactions/{address}` - Transaction history
- `POST /api/v1/blockchain/mine` - Manually mine block

### Operations
- `GET /api/v1/operations/stats` - Operation statistics
- `POST /api/v1/operations/cycle` - Execute operation cycle
- `GET /api/v1/operations/cycles` - Cycle history

### System Management
- `POST /api/v1/system/verify-integrity` - Verify system integrity
- `GET /api/v1/system/export` - Export complete system state

---

## 📁 Project Structure

```
nuclear-intelligence/
├── core/
│   ├── nuclear_intelligence.py    # Core AI engine
│   └── operation_loop.py          # Operation pipeline
├── blockchain/
│   └── virtual_ledger.py          # Virtual blockchain
├── api/
│   └── main.py                    # FastAPI application
├── knowledge_base/
│   ├── nuclear_knowledge_base.json
│   └── faiss_index/
├── scripts/
│   ├── initialize_knowledge_base.py
│   ├── run_operation_cycle.py
│   ├── verify_blockchain.py
│   ├── export_state.py
│   └── sync_huggingface.py
├── .github/workflows/
│   └── operation-loop.yml         # GitHub Actions CI/CD
├── config/
├── utils/
├── tests/
├── docs/
├── Dockerfile
├── requirements.txt
├── .env.template
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | Hugging Face API token | - |
| `GITHUB_TOKEN` | GitHub personal access token | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `LLM_MODEL_LARGE` | Large LLM model | gpt-4-turbo |
| `SCHEDULER_INTERVAL_MINUTES` | Operation loop interval | 45 |
| `FEATURE_HUMAN_IN_THE_LOOP` | Enable human review | true |
| `API_HOST` | API server host | 0.0.0.0 |
| `API_PORT` | API server port | 8000 |

---

## 🔄 Continuous Integration

### GitHub Actions Workflow

The project includes automated CI/CD via `.github/workflows/operation-loop.yml`:

- **Scheduled Execution**: Runs every 45 minutes
- **Automatic Sync**: Pushes changes to GitHub and Hugging Face
- **Keep-Alive**: Pings Hugging Face Space every 25 minutes
- **Logging**: Stores execution logs as artifacts

### Deployment to Hugging Face Space

1. Create a new Space with Docker template
2. Connect GitHub repository
3. Set secrets (HF_TOKEN, OPENAI_API_KEY, etc.)
4. Enable "Always On" for continuous operation

---

## 📈 Monitoring & Analytics

### Execution Statistics
- Total cycles executed
- Successful vs failed cycles
- Questions generated
- Answers generated
- NES tokens minted
- Average scientific accuracy

### Blockchain Metrics
- Chain length
- Pending transactions
- Total NES minted
- Last block hash
- Integrity verification status

### Knowledge Base Metrics
- Total entries
- Categories covered
- Last update timestamp
- Vector database size

---

## 🔐 Security Considerations

1. **API Keys**: Store all credentials in `.env` (never commit)
2. **Blockchain**: Virtual ledger uses HMAC signatures
3. **Data Privacy**: No personal data collection
4. **Rate Limiting**: Implement API rate limits in production
5. **Access Control**: Add authentication for sensitive endpoints

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=core --cov=blockchain tests/
```

---

## 📚 Knowledge Domains

The system covers comprehensive nuclear energy knowledge:

- **Nuclear Physics**: Fission, fusion, neutron physics, transmutation
- **Reactor Engineering**: Gen II/III/IV, SMR, molten salt, PWR, BWR
- **Safety & Management**: Non-proliferation, waste disposal, IAEA standards
- **Economics**: LCOE, PPA contracts, tokenized uranium, energy credits
- **Modern Applications**: AI data centers, desalination, hydrogen, load-following
- **AI Integration**: Knowledge tokenization, blockchain backing, governance

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👤 Developer

**Qalam** - Original developer and architect

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review operation cycle logs

---

## 🎯 Roadmap

- [ ] Integration with external blockchain networks
- [ ] Advanced RAG with semantic search
- [ ] Multi-model ensemble for better accuracy
- [ ] Governance token system
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Advanced visualization dashboard
- [ ] Integration with research institutions

---

## 🌟 Acknowledgments

- OpenAI for GPT models
- Hugging Face for infrastructure and models
- ArXiv for academic paper access
- LangChain for RAG framework
- FastAPI for web framework

---

**Nuclear Intelligence**: Transforming scientific knowledge into economic value through AI and blockchain. 🚀
