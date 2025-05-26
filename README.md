# Astarion 🧛

<p align="center">
  <img src="docs/astarion-logo.png" alt="Astarion Logo" width="200"/>
</p>

<p align="center">
  <strong>An intelligent LLM-powered assistant for RPG character creation and rule validation</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue.svg" alt="Python 3.13+"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"/>
  <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status: Alpha"/>
</p>

---

## 🌟 Features

- **🔍 Complete Rule Validation**: Every character choice validated against official rules
- **📚 Source Citations**: Every validation includes book and page references
- **⚡ Build Optimization**: MinMax strategies and synergy suggestions
- **🤖 Intelligent PDF Processing**: Automatically extract rules from uploaded rulebooks
- **🎯 Multi-System Support**: D&D 5e, Pathfinder, and more
- **🔌 VTT Integration**: Export to Roll20, FoundryVTT, and other platforms

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 14+ (optional, for production)
- Redis 6+ (optional, for caching)
- Qdrant (for vector storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/astarion.git
cd astarion
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Install PyKnow (rule engine):
```bash
pip install git+https://github.com/buguroo/pyknow.git
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Initialize the database:
```bash
alembic upgrade head
```

### Basic Usage

#### CLI Interface

```bash
# Validate a character file
astarion validate character.json --system dnd5e

# Create a character interactively
astarion create-character --interactive

# Add a rulebook to the system
astarion add-rulebook "Players_Handbook.pdf" --system dnd5e
```

#### Python API

```python
from astarion import CharacterValidator, RulebookProcessor

# Validate a character
validator = CharacterValidator(system="dnd5e")
result = await validator.validate_character(character_data)

# Process a rulebook
processor = RulebookProcessor()
await processor.process_pdf("Players_Handbook.pdf", system="dnd5e")
```

## 🏗️ Architecture

Astarion uses a multi-agent orchestrated architecture:

```mermaid
graph TB
    subgraph "User Interface"
        UI[Web/CLI Interface]
    end
    
    subgraph "Astarion Core"
        O[LangGraph Orchestrator]
        MCP[MCP Integration Layer]
    end
    
    subgraph "Specialized Agents"
        SA[Stats Agent]
        EA[Equipment Agent]
        LA[Lore Agent]
        VA[Validation Agent]
        OA[Optimization Agent]
    end
    
    subgraph "Knowledge Systems"
        RAG[RAG Pipeline]
        PK[PyKnow Rule Engine]
        VDB[(Vector Database)]
        RE[Rule Repository]
    end
    
    UI --> O
    O --> MCP
    MCP --> SA & EA & LA & VA & OA
    SA & EA & LA & VA & OA --> RAG
    SA & EA & LA & VA & OA --> PK
    RAG --> VDB
    PK --> RE
```

### Key Components

- **LangGraph Orchestrator**: Manages workflow and agent coordination
- **Specialized Agents**: Stats, Equipment, Lore, Validation, and Optimization agents
- **MCP Servers**: Standardized rule access via Model Context Protocol
- **RAG Pipeline**: Intelligent PDF processing and semantic search
- **PyKnow Engine**: Deterministic rule execution with explanations

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_validator.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Starting Development Server

```bash
# Start the API server
uvicorn src.api.main:app --reload

# Start the CLI in development mode
python -m src.cli.main
```

## 📦 Project Structure

```
astarion/
├── src/
│   ├── agents/          # LangGraph agents
│   ├── core/           # Core models and orchestration
│   ├── mcp/            # Model Context Protocol servers
│   ├── rag/            # RAG pipeline and PDF processing
│   ├── cli/            # CLI interface
│   ├── validation/     # Validation engine
│   └── utils/          # Utilities and helpers
├── tests/              # Test suite
├── docs/               # Documentation
└── config/             # Configuration files
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Documentation

- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [Architectural Design](docs/ARCHITECTURAL_DESIGN.md)
- [Domain Knowledge](docs/DOMAIN_KNOWLEDGE.md)
- [Integration Patterns](docs/INTEGRATION_PATTERNS.md)
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)

## 🛡️ Security

- All PDF uploads are scanned and validated
- API rate limiting prevents abuse
- No character data stored without explicit consent
- Respect for publisher copyrights

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The tabletop RPG community for inspiration and feedback
- LangChain and LangGraph teams for excellent frameworks
- All contributors who help make Astarion better

## 🚧 Status

Astarion is currently in **Phase 1: Foundation** development. Core functionality is being implemented with a focus on D&D 5e support.

### Current Features
- ✅ Basic character validation
- ✅ CLI interface
- 🚧 PDF rulebook processing
- 🚧 LangGraph orchestration
- 📅 Web interface (coming in Phase 3)

## 💬 Support

- Discord: [Join our server](https://discord.gg/astarion)
- Issues: [GitHub Issues](https://github.com/your-org/astarion/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/astarion/discussions)