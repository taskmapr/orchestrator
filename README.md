# TaskMapr Orchestrator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Backed by MIT Sandbox](https://img.shields.io/badge/Backed_by-MIT_Sandbox-A31F34.svg)](https://innovation.mit.edu/entrepreneurship-2/mit-sandbox-innovation-fund/)

**AI agent orchestration backend for TaskMapr UI Overlay**

A production-ready FastAPI server that powers TaskMapr's AI capabilities with OpenAI Agents SDK, Supabase persistence, and rich contextual awareness.

## ✨ Features

- 🤖 **OpenAI Agents SDK integration** - Full agent capabilities with reasoning and tool use
- 🌐 **TaskMapr context support** - Rich context from DOM elements, page state, and navigation
- 🔄 **SSE streaming** - Real-time streaming responses with typed events
- 🗄️ **Supabase integration** - Persistent conversation history and sessions
- 🔧 **MCP tools** - Extensible tool system for domain-specific workflows
- 🔐 **JWT authentication** - Secure Supabase token verification
- 🎯 **Zero-config mode** - Works standalone for development

## Architecture

```
┌─────────────────────┐
│   TaskMapr Client   │
│   (Browser)         │
└──────────┬──────────┘
           │ HTTPS/SSE
           ▼
┌─────────────────────┐
│   FastAPI Server    │
│  ┌───────────────┐  │
│  │ TaskMapr      │  │
│  │ Endpoint      │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ OpenAI Agents │  │
│  │ SDK Runner    │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ MCP Tools     │  │
│  │ + Memory      │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Supabase          │
│   (PostgreSQL)      │
└─────────────────────┘
```

## Project Structure

```
orchestrator/
├── app/
│   ├── __init__.py
│   ├── server.py           # Main FastAPI application
│   ├── config.py           # Configuration and environment
│   ├── auth.py             # Authentication helpers
│   ├── db.py               # Database setup
│   └── endpoints/
│       ├── __init__.py
│       ├── chat.py         # Legacy chat endpoint
│       ├── stream.py       # Legacy stream endpoint
│       └── taskmapr.py     # TaskMapr orchestrator endpoint
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required environment variables:**
```bash
OPENAI_API_KEY=sk-...           # OpenAI API key
SUPABASE_DB_URL=postgresql://...# PostgreSQL connection string
SUPABASE_URL=https://...        # Supabase project URL
SUPABASE_JWT_SECRET=...         # JWT secret (or use JWKS)
```

### 2. Run Server

```bash
uvicorn app.server:app --reload --port 8000
```

Server will be available at `http://localhost:8000`

### 3. Connect TaskMapr Client

```tsx
import { createTaskMaprClient } from '@taskmapr/ui-overlay';

const taskmapr = createTaskMaprClient('http://localhost:8000', {
  orchestrator: {
    orchestrator: new TaskMaprOrchestrator({
      apiBaseUrl: 'http://localhost:8000',
      getAccessToken: () => yourSupabaseToken,
    }),
  },
});
```

## API Reference

### TaskMapr Orchestrator (Streaming)

**`POST /api/taskmapr/orchestrate`**

Rich context streaming endpoint for TaskMapr integration.

**Request Body:**
```typescript
{
  prompt: string;                    // User message
  history?: Message[];               // Conversation history
  domElements?: DomElement[];        // Visible UI elements
  pageContext?: {                    // Current page info
    pathname: string;
    title: string;
  };
  sessionId?: string;                // Optional session ID
}
```

**Response:** SSE stream with typed events:
```typescript
// Text generation
{ type: 'text_delta', data: { delta: string } }

// Agent reasoning
{ type: 'reasoning_start', data: { content: string } }
{ type: 'reasoning_done', data: { content: string } }

// Tool execution
{ type: 'tool_call_started', data: { name: string, args: any } }
{ type: 'tool_call_completed', data: { result: any } }

// UI actions
{ type: 'actions', data: { highlight?: string, navigate?: string } }

// Completion
{ type: 'complete', data: { sessionId: string } }
```

### Health & Legacy Endpoints

- **`GET /`** - Root health check
- **`GET /health`** - Load balancer health check
- **`POST /api/chat/{session_key}`** - Non-streaming chat (legacy)
- **`GET /api/stream/{session_key}`** - Query param streaming (legacy)
- **`GET /api/history/{session_key}`** - Conversation history

## How It Works

The orchestrator enriches every AI interaction with rich contextual awareness:

### 🎯 Context Enrichment

**1. Page Context**
- Current URL and title
- Active navigation state
- User's current task/workflow

**2. DOM Snapshots**
- All visible interactive elements
- Element IDs, classes, ARIA labels
- Button text, input placeholders, form state
- Position and visibility metadata

**3. Conversation Memory**
- Full message history with Supabase persistence
- Cross-session continuity
- User preferences and patterns

### Example: Agent System Prompt

Every request automatically includes:

```
═══════════════════════════════════════════════════════════════
TASKMAPR CONTEXT - Web Application State
═══════════════════════════════════════════════════════════════

📍 Current Page:
  • Path: /create-model
  • Title: Create Abaqus Model
  
🎯 Interactive Elements (15 visible):
  • #submit-button "Create Model" (button, interactive)
  • #material-select "Select Material" (combobox, has-options)
  • #geometry-input "Enter dimensions" (textbox, empty)
  • #help-docs "View Documentation" (link)
  
💬 Recent Context:
  • User asked about material properties 2 messages ago
  • Steel material tutorial walkthrough active
  
💡 Instructions:
  • Reference visible elements when guiding user
  • Use available tools for domain-specific tasks
  • Suggest next steps based on current page context
```

**What the agent knows:**
- ✅ Exactly what UI elements the user sees
- ✅ What actions are currently possible
- ✅ The user's navigation history and intent
- ✅ Previous conversation context across sessions

## 🔧 Development

### Adding New Endpoints

1. Create endpoint file in `app/endpoints/`
2. Import and register in `app/server.py`

```python
from app.endpoints.my_endpoint import create_my_endpoint

my_route = create_my_endpoint(...)
app.post("/api/my-route")(my_route)
```

### Adding MCP Tools

Extend the agent with domain-specific tools in `app/server.py`:

```python
from your_tools import CustomWorkflowTool

tool_filter = create_static_tool_filter(
    allowed_tool_names=[
        "search_documentation",
        "create_workflow",
        "your_custom_tool",
    ]
)

# Tools are automatically available to the agent
```

### Database Schema

Supabase tables are created automatically:

```sql
-- Session management
CREATE TABLE agent_sessions (
  session_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- OpenAI Agents SDK creates additional tables:
-- - agent_threads (conversation threads)
-- - agent_messages (message history)
-- - agent_runs (execution tracking)
```

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t taskmapr-orchestrator .
docker run -p 8000:8000 --env-file .env taskmapr-orchestrator
```

### Production Checklist

**Security & Auth:**
- ✅ Set `SUPABASE_DB_URL` with SSL enabled
- ✅ Use JWKS instead of `JWT_SECRET` when possible
- ✅ Configure `SUPABASE_DB_SSL_ROOT_CERT` if using custom certs
- ✅ Set strict `CORS` origins (no wildcards)

**Infrastructure:**
- ✅ Configure load balancer health checks → `/health`
- ✅ Set up logging aggregation (JSON logs)
- ✅ Enable auto-scaling based on connection count
- ✅ Configure session timeout appropriately

**Optional:**
- ✅ Set `MCP_BASE_URL` for external MCP server
- ✅ Configure custom OpenAI base URL if needed

## 📊 Monitoring

### Logs

Structured logging for all important events:

```
[TaskMapr] Starting stream for session taskmapr_user123_1234567890
[TaskMapr] Page: /create-model (15 interactive elements)
[TaskMapr] Tool call: search_documentation(query="steel properties")
[TaskMapr] Stream completed - 2.4s, 1247 tokens
[TaskMapr] Client disconnected for session ...
```

### Key Metrics

**Performance:**
- Stream duration (p50, p95, p99)
- Time to first token
- Tokens per second

**Usage:**
- Active sessions (concurrent)
- Messages per session
- Tool call frequency by type

**Reliability:**
- Error rate by endpoint
- Database connection health
- Session persistence success rate

## 🐛 Troubleshooting

### SSL Connection Issues

If you see SSL errors connecting to Supabase:

```bash
# Option 1: Use built-in CA bundle (automatic, recommended)
# Just works with standard Supabase URLs

# Option 2: Disable SSL verification (dev/testing only)
SUPABASE_DB_ALLOW_INVALID_SSL=true

# Option 3: Provide custom certificate
SUPABASE_DB_SSL_ROOT_CERT=/path/to/ca-certificate.crt
```

### MCP Tools Not Loading

Server continues gracefully without MCP:

```
⚠️  Warning: Could not import MCP server
    Reason: Module 'your_mcp_tools' not found
    Impact: Domain-specific tools will not be available
    Action: Agent will continue with base capabilities
```

### Session Persistence Disabled

Works in-memory for development:

```
⚠️  Warning: Could not create SQLAlchemySession
    Reason: Database connection failed
    Impact: Sessions will not persist across restarts
    Action: Continuing with in-memory sessions only
```

### Common Issues

**Authentication failures:**
- Verify `SUPABASE_JWT_SECRET` matches your project
- Check token expiration (default 1 hour)
- Ensure client is sending `Authorization: Bearer <token>`

**Streaming breaks/timeouts:**
- Check network keeps alive connections open
- Verify load balancer timeout settings (recommend 300s+)
- Look for client-side disconnections in logs

## 🧪 Testing

### Local Testing

```bash
# Start development server
uvicorn app.server:app --reload --log-level debug

# Test health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test SSE streaming
curl -X POST http://localhost:8000/api/taskmapr/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"prompt":"Hello","sessionId":"test-123"}' \
  --no-buffer
```

### Integration Testing

Connect from TaskMapr UI Overlay:

```typescript
import { TaskMaprOrchestrator } from '@taskmapr/ui-overlay';

const orchestrator = new TaskMaprOrchestrator({
  apiBaseUrl: 'http://localhost:8000',
  getAccessToken: async () => {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? '';
  },
});

// Use in createTaskMaprClient config
const taskmapr = createTaskMaprClient('', {
  orchestrator: { orchestrator },
});
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **TaskMapr UI Overlay**: https://www.npmjs.com/package/@taskmapr/ui-overlay
- **OpenAI Agents SDK**: https://github.com/openai/openai-agents-python
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

## 💬 Support

For issues or questions:

1. **Check logs first** - Server logs provide detailed error context
2. **Verify environment** - Ensure all required variables are set
3. **Test health endpoints** - Confirm basic connectivity
4. **Review integration guide** - See TaskMapr UI Overlay docs

---

**Built with ❤️ by TaskMapr** • Intelligent AI orchestration for modern web apps
