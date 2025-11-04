"""
Main FastAPI Application

Agent Orchestrator Server with TaskMapr integration, OpenAI Agents SDK, and MCP tools.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from openai import AsyncOpenAI

from agents.agent import Agent
from agents.model_settings import ModelSettings
from agents.run import Runner, RunConfig, CallModelData, ModelInputData
from agents.mcp import MCPServerSse, MCPServerSseParams, create_static_tool_filter

from app.config import MCP_SERVER_URL, MCP_BASE_URL, DISABLE_AUTH
from app.auth import authenticate_supabase_user
from app.db import engine, ensure_session_row, make_sqlalchemy_session
from app.endpoints.taskmapr import create_taskmapr_endpoint


# ────────────────────────────────────────────────────────────────────────────────
# MCP Server Setup
# ────────────────────────────────────────────────────────────────────────────────

# Import and initialize the MCP server first (before lifespan)
mcp_server_available = False
try:
    from mcp_runtime.server import server as mcp_server_instance
    mcp_server_available = True
    print("✓ MCP server module imported successfully")
except Exception as e:
    print(f"⚠ Warning: Could not import MCP server: {e}")
    print("  MCP tools will not be available")
    mcp_server_instance = None


# Background task to connect to MCP server after startup
async def connect_mcp_background():
    """Connect to the MCP server after the main app has started."""
    if not mcp_server_available:
        print("⊘ Skipping MCP connection - server not available")
        return
    
    # Wait for the server to be fully started and accepting connections
    await asyncio.sleep(2.0)
    
    try:
        await mcp.connect()
        print(f"✓ MCP server connected successfully to {MCP_SERVER_URL}")
    except Exception as e:
        print(f"⚠ Warning: Failed to connect to MCP server at {MCP_SERVER_URL}: {e}")
        print("  Agent will continue without MCP tools")


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP server connection lifecycle."""
    print("\n" + "="*70)
    print("🚀 Agent Orchestrator Server Starting")
    print("="*70)
    
    # Show authentication status
    if DISABLE_AUTH:
        print("⚠️  AUTHENTICATION DISABLED - Development mode")
        print("   All requests will use test user without JWT verification")
    else:
        print("✓ Authentication enabled")
    
    # Startup: Launch background task to connect to MCP server
    if mcp_server_available:
        asyncio.create_task(connect_mcp_background())
        print("✓ MCP connection task scheduled")
    else:
        print("⊘ Skipping MCP connection - server not available")
    
    print("="*70 + "\n")
    
    yield  # App runs here
    
    # Shutdown
    print("\n" + "="*70)
    print("🛑 Agent Orchestrator Server Shutting Down")
    print("="*70)
    
    if mcp_server_available:
        try:
            await mcp.cleanup()
            print("✓ MCP server disconnected")
        except Exception as e:
            print(f"⚠ Warning: Error disconnecting MCP server: {e}")
    
    print("="*70 + "\n")


# ────────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ────────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agent Orchestrator Server",
    description="FastAPI server with OpenAI Agents SDK, TaskMapr, and MCP tools",
    version="1.0.0",
    lifespan=lifespan,
)


# Mount the MCP server if available
if mcp_server_available and mcp_server_instance is not None:
    try:
        mcp_app = mcp_server_instance.sse_app()
        app.mount("/mcp", mcp_app)
        print("✓ MCP server mounted successfully at /mcp")
    except Exception as e:
        print(f"⚠ Warning: Could not mount MCP server: {e}")
        print("  MCP tools will not be available")
        mcp_server_available = False


# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────────────────────────────────────────────
# MCP Tool Configuration
# ────────────────────────────────────────────────────────────────────────────────

print(f"MCP Server configured to connect to: {MCP_SERVER_URL}")

mcp_params = MCPServerSseParams(
    url=MCP_SERVER_URL,
)

# Create static tool filter for allowed tools
tool_filter = create_static_tool_filter(
    allowed_tool_names=[
        "answer_abaqus_question",
        "search_abaqus_documents",
        "list_steel_scaffolds",
        "download_supabase_scaffold",
        "scaffold_lipped_cee_column",
        "prepare_rescale_job",
        "submit_rescale_job",
        "run_rescale_generate_input",
        "handoff_to_expert",
        "get_manual_task_status",
        "submit_execution_plan",
        "validate_abaqus_keywords",
    ]
)

mcp = MCPServerSse(
    params=mcp_params,
    name="Abaqus_MCP_Server",
    tool_filter=tool_filter,
)


# ────────────────────────────────────────────────────────────────────────────────
# Agent Configuration
# ────────────────────────────────────────────────────────────────────────────────

# Only include MCP servers if MCP is available and connected
mcp_servers_list = []
if mcp_server_available:
    mcp_servers_list = [mcp]

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions=(
        "You are a helpful AI assistant with access to web page context. "
        "You can help users navigate web applications, answer questions, and provide guidance. "
        "When you see DOM elements and page context, use that information to provide helpful, actionable responses. "
        "Be concise and user-friendly."
        + (" You have access to MCP tools for Abaqus workflows." if mcp_server_available else "")
    ),
    model="gpt-4o-mini",
    mcp_servers=mcp_servers_list,  # Empty list if MCP not available
    model_settings=ModelSettings(
        store=True,  # <-- enables memory (persisted by SQLAlchemySession)
        # Note: reasoning parameters not supported by gpt-4o-mini
    ),
)


# ────────────────────────────────────────────────────────────────────────────────
# Run Configuration
# ────────────────────────────────────────────────────────────────────────────────

def make_run_config(session_key: str, user_id: str) -> RunConfig:
    """Create a run configuration with user context for manual handoffs."""

    user_context_marker = f"USER_CONTEXT::{user_id}"
    user_context_text = (
        f"{user_context_marker}\n"
        f"Supabase user_id: {user_id}\n"
        f"Session key: {session_key}\n"
        "Always pass this user_id when using manual handoff tools such as "
        "handoff_to_expert or get_manual_task_status."
    )

    def inject_user_context(call_data: CallModelData[Any]) -> ModelInputData:
        model_data = call_data.model_data
        items = list(model_data.input or [])

        for item in items:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                text = block.get("text")
                if isinstance(text, str) and user_context_marker in text:
                    return model_data

        system_message = {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": user_context_text,
                }
            ],
        }

        model_data.input = [system_message] + items
        return model_data

    return RunConfig(
        trace_metadata={
            "__trace_source__": "agents-sdk",
            "session_key": session_key,
            "user_id": user_id,
        },
        call_model_input_filter=inject_user_context,
    )


# ────────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "service": "abaqus-agent-orchestrator",
        "version": "1.0.0",
        "mcp_available": mcp_server_available,
        "endpoints": {
            "health": "/health",
            "taskmapr": "/api/taskmapr/orchestrate",
        }
    })


@app.get("/health")
async def health():
    """Health check endpoint for load balancers."""
    return JSONResponse({
        "status": "ok",
        "db": "connected" if engine else "not configured",
        "mcp": "available" if mcp_server_available else "unavailable",
    })


# ────────────────────────────────────────────────────────────────────────────────
# TaskMapr Orchestrator Endpoint
# ────────────────────────────────────────────────────────────────────────────────

taskmapr_orchestrate = create_taskmapr_endpoint(
    authenticate_supabase_user=authenticate_supabase_user,
    ensure_session_row=ensure_session_row,
    make_sqlalchemy_session=make_sqlalchemy_session,
    make_run_config=make_run_config,
    orchestrator_agent=orchestrator_agent,
    Runner=Runner,
)

app.post("/api/taskmapr/orchestrate")(taskmapr_orchestrate)


# ────────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
