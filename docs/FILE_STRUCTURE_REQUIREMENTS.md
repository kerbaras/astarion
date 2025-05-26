```
./src/astarion/
├── __init__.py          # ALWAYS include version
├── agents/
│   ├── __init__.py      # ALWAYS export all agents
│   ├── base.py          # NEVER instantiate directly
│   └── {agent_name}.py  # ONE agent per file
├── mcp/
│   ├── __init__.py
│   ├── client.py        # Shared MCP client
│   └── servers/
│       └── {system}/    # ONE directory per game system
│           ├── __init__.py
│           └── server.py
├── rules/
│   ├── __init__.py
│   ├── engine.py        # Shared rule engine
│   └── {system}/        # ONE directory per game system
├── rag/
│   ├── __init__.py
│   ├── pipeline.py      # Main pipeline orchestrator
│   ├── extractors/      # PDF extraction strategies
│   ├── chunkers/        # Document chunking logic
│   └── embedders/       # Embedding generation
└── types/               # ALL type definitions here
    ├── __init__.py
    ├── character.py
    ├── validation.py
    └── rules.py
```