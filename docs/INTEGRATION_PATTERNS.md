# INTEGRATION PATTERNS & COMPONENT COMMUNICATION

## COMPONENT INTERACTION OVERVIEW

### Communication Flow
```
External Request
    ↓
API Gateway (FastAPI)
    ↓
LangGraph Orchestrator
    ↓ (parallel branches)
    ├→ MCP Clients → Rule Servers
    ├→ RAG Pipeline → Vector Database
    └→ Validation Engine → PyKnow Rules
    ↓
Response Aggregation
    ↓
Client Response
```

### Core Integration Principles
1. **Loose Coupling**: Components interact through well-defined interfaces
2. **Event-Driven**: Asynchronous message passing where possible
3. **Fail-Safe**: Graceful handling of component failures
4. **Stateless**: No shared state between components
5. **Observable**: All interactions can be monitored and traced

## LANGGRAPH ORCHESTRATION PATTERNS

### State Management Strategy
The orchestrator maintains a single source of truth for character state:

```
CharacterState {
    character_data: Current character information
    validation_results: Accumulated validation results
    processing_history: What has been processed
    pending_operations: What still needs processing
    context: User preferences and settings
}
```

### Agent Communication Pattern
Agents don't communicate directly but through state mutations:

1. **Agent A** reads state, performs operation, updates state
2. **Orchestrator** routes updated state to next agent
3. **Agent B** reads updated state, continues processing

This ensures:
- No tight coupling between agents
- Clear audit trail of changes
- Easy testing of individual agents
- Ability to replay/debug workflows

### Conditional Routing Logic
```
State Analysis → Routing Decision → Next Agent(s)

Examples:
- If validation errors exist → Route to error handler
- If optimization requested → Route to optimization agent
- If multiclass detected → Route to prerequisite checker
```

## MCP INTEGRATION PATTERNS

### Server Discovery
```
1. System starts → Scan for available MCP servers
2. Each server registers its capabilities
3. Orchestrator maintains server registry
4. Clients request appropriate server for game system
```

### Request Routing
```
Character System = "dnd5e"
    ↓
Find MCP Server for "dnd5e"
    ↓
Route validation requests to that server
    ↓
Server responds with validation + sources
```

### Tool Registration Pattern
Each MCP server exposes:
- **Validation Tools**: Check specific rules
- **Query Tools**: Search for rules
- **Calculation Tools**: Compute derived values
- **Resource Endpoints**: Access static data

## RAG PIPELINE INTEGRATION

### Document Processing Flow
```
PDF Upload
    ↓
Queue for Processing (Redis Queue)
    ↓
PDF Processor (Worker)
    ↓
Chunk Storage (Vector DB)
    ↓
Rule Extraction (Background)
    ↓
PyKnow Rule Generation
```

### Query Processing Pattern
```
User Query: "Can a dwarf be a bladesinger?"
    ↓
Query Expansion: Add synonyms, related terms
    ↓
Vector Search: Find relevant chunks
    ↓
Reranking: Sort by relevance
    ↓
Context Assembly: Build prompt with sources
    ↓
LLM Generation: Create cited response
```

### Hybrid Search Strategy
Combines multiple retrieval methods:
1. **Semantic Search**: Vector similarity for concepts
2. **Keyword Search**: Exact term matching
3. **Metadata Filtering**: System, book, section
4. **Rule ID Lookup**: Direct rule retrieval

## VALIDATION ENGINE INTEGRATION

### Multi-Stage Validation Flow
```
Raw Input
    ↓
Schema Validation (Pydantic)
    ↓
Business Rule Validation (PyKnow)
    ↓
Cross-Reference Validation (MCP)
    ↓
Optimization Analysis (Constraint Solver)
    ↓
Final Report Generation
```

### Rule Engine Communication
PyKnow integration follows fact-based pattern:
```
Convert Character → Facts
Load Relevant Rules → Knowledge Base
Execute Forward Chaining → Conclusions
Extract Violations → Validation Results
```

### Validation Result Aggregation
Results from multiple sources are merged:
- **Priority**: Errors > Warnings > Info
- **Deduplication**: Same rule from multiple sources
- **Grouping**: Related issues together
- **Sorting**: By severity and category

## EXTERNAL SYSTEM INTEGRATION

### API Gateway Patterns

#### REST API Design
```
POST /api/v1/characters/validate
{
    "system": "dnd5e",
    "character": { ... },
    "options": {
        "strict_mode": true,
        "include_optimization": true
    }
}
```

#### GraphQL Alternative
```graphql
mutation ValidateCharacter($character: CharacterInput!) {
    validateCharacter(character: $character) {
        valid
        errors {
            rule
            message
            source { book page }
        }
        suggestions {
            optimization
            impact
        }
    }
}
```

#### WebSocket for Real-time
```
Client connects → Subscribe to character session
Character changes → Instant validation
Results stream → Update UI immediately
```

### VTT Integration Patterns

#### Plugin Architecture
```
VTT Plugin (Roll20, Foundry)
    ↓
Astarion API Client
    ↓
Character Data Transformation
    ↓
Validation Request
    ↓
Results Interpretation
    ↓
VTT UI Update
```

#### Data Format Translation
Each VTT has its own format:
- **Roll20**: JSON with specific schema
- **Foundry**: Different JSON structure
- **Fantasy Grounds**: XML format

Astarion provides adapters for each.

### Authentication & Authorization

#### API Key Pattern
```
Request Header: Authorization: Bearer <api-key>
    ↓
Validate API Key
    ↓
Check Rate Limits
    ↓
Log Usage
    ↓
Process Request
```

#### OAuth2 Flow (Future)
For deeper integrations:
1. VTT requests access
2. User authorizes Astarion
3. Token exchange
4. Scoped access to validations

## EVENT-DRIVEN PATTERNS

### Internal Events
```
Events Published:
- character.created
- validation.completed
- rulebook.processed
- optimization.generated

Subscribers:
- Analytics service
- Cache invalidation
- Notification system
- Audit logger
```

### Webhook System
External systems can subscribe:
```
Subscription: {
    url: "https://example.com/webhook",
    events: ["validation.completed"],
    filters: { system: "dnd5e" }
}
```

### Event Payload Standard
```json
{
    "event_type": "validation.completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "character_id": "uuid",
        "validation_id": "uuid",
        "result": "valid",
        "error_count": 0
    },
    "metadata": {
        "api_version": "1.0",
        "system": "dnd5e"
    }
}
```

## CACHING STRATEGIES

### Multi-Level Cache
```
1. Browser Cache (if web UI)
2. CDN Cache (static resources)
3. API Gateway Cache (Redis)
4. Application Cache (in-memory)
5. Database Query Cache
```

### Cache Invalidation Patterns
- **Time-based**: TTL for different data types
- **Event-based**: Invalidate on rule updates
- **Version-based**: New rulebook versions
- **Selective**: Only affected rules

### Cached Data Types
- **Hot**: Frequently accessed rules (1hr TTL)
- **Warm**: Common character options (24hr TTL)
- **Cold**: Rarely used rules (7 day TTL)
- **Static**: Core rules (until version change)

## ERROR HANDLING PATTERNS

### Error Propagation
```
Component Error
    ↓
Catch and Log
    ↓
Determine if Recoverable
    ↓
If Yes: Retry with backoff
If No: Graceful degradation
    ↓
User-Friendly Error Message
```

### Fallback Strategies
- **MCP Unavailable**: Use cached rules
- **RAG Unavailable**: Use rule IDs only
- **PyKnow Unavailable**: Basic validation only
- **Database Unavailable**: Read-only mode

### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_SERVICE_UNAVAILABLE",
        "message": "Unable to perform complete validation",
        "details": "Advanced rule checking temporarily unavailable",
        "partial_results": { ... },
        "retry_after": 30
    }
}
```

## MONITORING & OBSERVABILITY

### Trace Context
Each request gets unique trace ID:
```
Trace-ID: 12345
    → API Gateway (span 1)
    → Orchestrator (span 2)
    → Stats Agent (span 3a)
    → MCP Call (span 4a)
    → Equipment Agent (span 3b)
    → Validation (span 5)
```

### Metrics Collection
Key metrics per component:
- **Latency**: Response time percentiles
- **Throughput**: Requests per second
- **Error Rate**: Failures per component
- **Saturation**: Resource utilization

### Health Check Endpoints
Each component exposes:
```
GET /health
{
    "status": "healthy",
    "checks": {
        "database": "ok",
        "redis": "ok",
        "mcp_servers": {
            "dnd5e": "ok",
            "pathfinder": "degraded"
        }
    }
}
```