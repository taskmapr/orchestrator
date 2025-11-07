# TaskMapr Orchestrator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Backed by MIT Sandbox](https://img.shields.io/badge/Backed_by-MIT_Sandbox-A31F34.svg)](https://innovation.mit.edu/entrepreneurship-2/mit-sandbox-innovation-fund/)

**AI agent orchestration backend for TaskMapr UI Overlay**

FastAPI server that powers TaskMapr's AI capabilities with OpenAI Agents SDK, Supabase persistence, and rich contextual awareness.

## Features

- OpenAI Agents SDK integration with reasoning and tool use
- Rich context from DOM elements, page state, and navigation
- SSE streaming with real-time typed events
- Supabase integration for persistent conversation history
- MCP tools for extensible domain-specific workflows
- JWT authentication via Supabase token verification
- Built-in knowledge tools for curated project briefs

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
│       └── taskmapr.py     # TaskMapr orchestrator endpoint
├── requirements.txt
├── .env.example
├── knowledge/             # Markdown knowledge packs consumed by the agent
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

The orchestrator enriches every AI interaction with contextual awareness:

- **Page Context**: Current URL, title, and navigation state
- **DOM Snapshots**: All visible interactive elements with IDs, classes, ARIA labels, and positions
- **Conversation Memory**: Full message history with Supabase persistence and cross-session continuity

The agent receives rich context including visible UI elements, page state, and conversation history to provide helpful, context-aware responses.

## Development

Add new endpoints in `app/endpoints/` and register in `app/server.py`. MCP tools can be added by configuring the tool filter in `app/server.py`. Supabase tables are created automatically by the OpenAI Agents SDK.

## Deployment

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
docker build -t taskmapr-orchestrator .
docker run -p 8000:8000 --env-file .env taskmapr-orchestrator
```

### Production Checklist

- Set `SUPABASE_DB_URL` with SSL enabled
- Use JWKS instead of `JWT_SECRET` when possible
- Configure load balancer health checks → `/health`
- Set strict CORS origins (no wildcards)

## Testing

```bash
uvicorn app.server:app --reload --log-level debug
curl http://localhost:8000/health
```

## License

MIT License - see LICENSE file for details.

## Links

- **TaskMapr UI Overlay**: https://www.npmjs.com/package/@taskmapr/ui-overlay
- **OpenAI Agents SDK**: https://github.com/openai/openai-agents-python
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

---

**Built with ❤️ by TaskMapr** • Intelligent AI orchestration for modern web apps
