# ASTARION ARCHITECTURAL DESIGN

## SYSTEM ARCHITECTURE OVERVIEW

### Core Architecture Pattern
Astarion uses a **Multi-Agent Orchestrated Architecture** where specialized agents collaborate through a central orchestrator to handle different aspects of character creation and validation.

```
User Request → Orchestrator → Specialized Agents → Knowledge Systems → Validated Response
```

### Key Architectural Decisions

1. **LangGraph as Orchestrator**: Chosen over alternatives for production stability and complex workflow support
2. **Model Context Protocol (MCP)**: Support multiple tools like memory-storage and others via mcp
3. **Hybrid RAG + Rule Engine**: Combines flexibility of LLMs with determinism of rule engines
4. **Plugin Architecture**: Index new game systems by adding them to the RAG db
5. **Event-Driven Processing**: Asynchronous, scalable design

## COMPONENT BREAKDOWN

### 1. ORCHESTRATION LAYER (LangGraph)

**Purpose**: Manages the flow of character creation and validation processes

**Key Responsibilities**:
- Route requests to appropriate agents
- Manage state throughout character creation
- Handle error recovery and retries
- Coordinate parallel processing
- Maintain conversation context

**Design Rationale**: LangGraph provides visual debugging, state persistence, and production-grade reliability that simpler frameworks lack.

### 2. AGENT SYSTEM

**Purpose**: Specialized intelligence for different domains

**Agent Types**:
- **Stats Agent**: Handles ability scores, modifiers, generation methods
- **Equipment Agent**: Manages items, proficiencies, encumbrance
- **Lore Agent**: Creates backgrounds, personalities, story hooks
- **Ruleset Agent**: Query RAG qdrant db for knowladge about the rules of the loaded systems
- **Validation Agent**: Ensures all rules are followed
- **Optimization Agent**: Suggests powerful build strategies

**Agent Collaboration Pattern**: Agents communicate through shared state, passing enriched character data between stages while maintaining independence.

### 3. MODEL CONTEXT PROTOCOL (MCP) LAYER

**Purpose**: Standardized interface between LLMs and game rule data

**Key Features**:
- Consistent API across different game systems
- Tool registration for rule queries
- Resource endpoints for static data
- Streaming support for large responses

**Why MCP**: Provides a vendor-neutral way to expose game rules, allowing any LLM to access Astarion's knowledge base.

### 4. KNOWLEDGE SYSTEMS

#### 4.1 RAG Pipeline
**Purpose**: Convert rulebooks into searchable, intelligent knowledge

**Processing Flow**:
1. PDF Ingestion: Extract text, tables, images
2. Intelligent Chunking: Separate spells, feats, rules
3. Embedding Generation: Create semantic representations
4. Vector Storage: Enable similarity search
5. Metadata Enrichment: Add classifications, prerequisites

**Design Choice**: Hybrid approach using both PyMuPDF and pdfplumber ensures accurate extraction of both text and tabular data.

#### 4.2 PyKnow Rule Engine
**Purpose**: Deterministic execution of game rules

**Key Capabilities**:
- Forward-chaining inference
- Fact-based reasoning
- Rule priority handling
- Conflict resolution
- Explanation generation

**Why PyKnow**: Provides traceable, deterministic rule execution with the ability to explain why decisions were made.

### 5. VALIDATION SYSTEM

**Multi-Stage Validation**:
1. **Syntax**: Basic rule structure and format
2. **Semantic**: Rule interactions and consistency
3. **Contextual**: Character-specific validity
4. **Optimization**: Build effectiveness analysis

**Validation Philosophy**: Every validation includes source citations, making disputes resolvable by checking the referenced material.

## DATA FLOW ARCHITECTURE

### Character Creation Flow
```
1. User Input
   ↓
2. Input Validation (Schema)
   ↓
3. Orchestrator Initialization
   ↓
4. Agent Processing (Parallel where possible)
   ├─→ Stats Generation
   ├─→ Race Selection
   └─→ Background Creation
   ↓
5. Validation Checkpoint
   ↓
6. Equipment & Features
   ↓
7. Final Validation
   ↓
8. Optimization Suggestions
   ↓
9. Export/Display
```

### Rule Processing Flow
```
1. PDF Upload
   ↓
2. Content Extraction
   ├─→ Text Extraction
   ├─→ Table Recognition
   └─→ Image Analysis
   ↓
3. Intelligent Chunking
   ├─→ Spell Blocks
   ├─→ Class Features
   ├─→ Rule Sections
   └─→ Equipment Lists
   ↓
4. Dual Processing
   ├─→ RAG Pipeline (Semantic Search)
   └─→ Rule Extraction (PyKnow Rules)
   ↓
5. Validation & Testing
   ↓
6. Production Deployment
```

## SCALABILITY ARCHITECTURE

### Horizontal Scaling Strategy
- **Stateless Agents**: Can run multiple instances
- **Distributed Processing**: Rules processed in parallel
- **Cache Layers**: Redis for frequently accessed rules
- **Load Balancing**: Distribute requests across instances

### Performance Optimizations
- **Lazy Loading**: Rules loaded only when needed
- **Embedding Cache**: Pre-computed vectors for common queries
- **Rule Compilation**: PyKnow rules pre-compiled for speed
- **Async Everything**: Non-blocking operations throughout

## INTEGRATION ARCHITECTURE

### API Design Philosophy
- **RESTful Principles**: Standard HTTP methods and status codes
- **GraphQL Option**: For complex, nested character queries
- **WebSocket Support**: Real-time validation during creation
- **Webhook System**: Notify external systems of changes

### External System Integration
```
Astarion API
    ├─→ VTT Platforms (Roll20, Foundry)
    ├─→ Character Builders
    ├─→ Discord Bots
    ├─→ Mobile Apps
    └─→ Tournament Systems
```

## SECURITY ARCHITECTURE

### Key Security Measures
- **Input Sanitization**: All PDF uploads scanned and validated
- **Rule Isolation**: Each game system runs in isolated context
- **API Rate Limiting**: Prevent abuse and ensure fair usage
- **Audit Logging**: Track all rule changes and validations

### Data Privacy
- **No Character Storage**: Unless explicitly requested
- **Rulebook Licensing**: Respect publisher copyrights
- **User Anonymity**: No tracking without consent

## EXTENSIBILITY ARCHITECTURE

### Plugin System Design
```
New Game System Plugin
    ├── metadata.yaml      # System information
    ├── rules/            # PyKnow rule definitions
    ├── mcp/              # MCP server implementation
    ├── extractors/       # PDF parsing patterns
    └── tests/            # Validation tests
```

### Community Contribution Flow
1. Develop plugin following templates
2. Submit with test cases
3. Community validation period
4. Automated testing suite
5. Official integration

## FAILURE HANDLING ARCHITECTURE

### Graceful Degradation Strategy
- **Component Independence**: One service failure doesn't break others
- **Fallback Modes**: Basic validation when optimization unavailable
- **Partial Results**: Return what's possible rather than failing entirely
- **Clear Error Messages**: Explain what failed and why

### Recovery Mechanisms
- **Automatic Retries**: With exponential backoff
- **Circuit Breakers**: Prevent cascade failures
- **Health Checks**: Continuous monitoring
- **Self-Healing**: Automatic service restart

## MONITORING & OBSERVABILITY

### Key Metrics
- **Validation Accuracy**: Track rule application correctness
- **Response Time**: Character creation speed
- **API Usage**: Which rules/systems most queried
- **Error Rates**: Identify problematic rules or systems

### Debugging Features
- **Request Tracing**: Follow character through entire system
- **Rule Execution Logs**: See which rules fired and why
- **LangGraph Visualization**: Visual debugging of agent flows