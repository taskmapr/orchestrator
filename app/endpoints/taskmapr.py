"""
TaskMapr Orchestrator Endpoint for Agent Streaming

This module provides a streaming endpoint specifically designed for TaskMapr integration.
It accepts rich context (DOM elements, page state, history) and streams agent responses.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import Request, HTTPException, Header
from sse_starlette.sse import EventSourceResponse


# ────────────────────────────────────────────────────────────────────────────────
# TaskMapr Types
# ────────────────────────────────────────────────────────────────────────────────

class DOMElementSnapshot(BaseModel):
    id: str
    tagName: str
    textContent: str
    classNames: List[str]
    role: Optional[str] = None
    ariaLabel: Optional[str] = None
    ariaDescribedBy: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = None
    position: Dict[str, float]
    isInteractive: bool


class PageContext(BaseModel):
    pathname: str
    search: str = ""
    hash: str = ""
    title: str = ""


class WalkthroughContext(BaseModel):
    id: str
    currentStepIndex: int
    totalSteps: int
    currentStep: Dict[str, Any]


class HighlightAction(BaseModel):
    selector: str
    duration: Optional[int] = None


class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    highlight: Optional[List[HighlightAction]] = None


class AgentContextPackage(BaseModel):
    """Complete context package from TaskMapr client."""
    prompt: str
    history: List[Message]
    domElements: List[DOMElementSnapshot]
    pageContext: PageContext
    walkthroughContext: Optional[WalkthroughContext] = None
    customContext: Optional[Dict[str, Any]] = None
    timestamp: str
    sessionId: Optional[str] = None


class AgentAction(BaseModel):
    """Actions that can be returned to TaskMapr UI."""
    type: str  # 'navigate', 'highlight', 'startWalkthrough', 'scrollTo', 'custom'
    payload: Dict[str, Any]


# ────────────────────────────────────────────────────────────────────────────────
# Context Enhancement
# ────────────────────────────────────────────────────────────────────────────────

def build_taskmapr_system_context(context: AgentContextPackage) -> str:
    """
    Build a rich system context message from TaskMapr context package.
    This gives the agent awareness of the user's current page and available interactions.
    """
    # Extract interactive elements
    interactive_elements = [
        el for el in context.domElements
        if el.isInteractive
    ]

    # Extract ALL elements with IDs (for highlighting and reading text)
    all_elements_with_ids = [
        el for el in context.domElements
        if el.id and el.id.strip() and el.id != "root"
    ]

    # Build element descriptions for interactive elements
    element_descriptions = []
    for el in interactive_elements[:20]:  # Limit to top 20 to avoid token overload
        desc_parts = [f"#{el.id}" if el.id else el.tagName]
        if el.ariaLabel:
            desc_parts.append(f'"{el.ariaLabel}"')
        elif el.textContent:
            truncated = el.textContent[:50]
            desc_parts.append(f'"{truncated}"')
        if el.role:
            desc_parts.append(f"({el.role})")
        element_descriptions.append(" ".join(desc_parts))

    # Build lists for quick lookup
    available_ids = [el.id for el in all_elements_with_ids[:30]]
    ids_with_keywords: Dict[str, List[str]] = {}
    text_previews: Dict[str, str] = {}
    for el in all_elements_with_ids[:40]:
        text = (el.textContent or "").strip()
        if text and el.id:
            text_previews[el.id] = text[:200].replace("\n", " ")

        text_lower = text.lower()
        id_lower = el.id.lower() if el.id else ""
        # Check for common keywords including textual sections
        for keyword in [
            "comment",
            "post",
            "tag",
            "user",
            "search",
            "create",
            "export",
            "filter",
            "title",
            "body",
            "summary",
            "misc",
        ]:
            if keyword in id_lower or keyword in text_lower:
                if keyword not in ids_with_keywords:
                    ids_with_keywords[keyword] = []
                selector = f"#{el.id}"
                if selector not in ids_with_keywords[keyword]:
                    ids_with_keywords[keyword].append(selector)
    
    # Build walkthrough context if active
    walkthrough_info = ""
    if context.walkthroughContext:
        wt = context.walkthroughContext
        walkthrough_info = f"""
Active Walkthrough: {wt.id}
Current Step: {wt.currentStepIndex + 1} of {wt.totalSteps}
Step Details: {json.dumps(wt.currentStep, indent=2)}
"""
    
    # Build list of available routes/pages from context
    available_routes = []
    if context.pageContext.pathname == "/":
        available_routes = ["/", "/features", "/about"]
    else:
        # Extract routes from visible navigation elements
        for el in interactive_elements:
            if el.role == "link" or el.tagName.lower() == "a":
                href = getattr(el, "href", "") or ""
                if href.startswith("/"):
                    available_routes.append(href.split("?")[0].split("#")[0])
    
    # Build full system context
    system_context = f"""
═══════════════════════════════════════════════════════════════
TASKMAPR CONTEXT - Web Application State
═══════════════════════════════════════════════════════════════

📍 Current Page:
  • Path: {context.pageContext.pathname}
  • Title: {context.pageContext.title}
  • URL: {context.pageContext.pathname}{context.pageContext.search}{context.pageContext.hash}

🎯 Interactive Elements ({len(interactive_elements)} visible):
{chr(10).join(f"  • {desc}" for desc in element_descriptions)}

{'🔍 Available Element IDs for Highlighting: ' + ', '.join(available_ids[:15]) + ('...' if len(available_ids) > 15 else '') if available_ids else ''}

{'🎯 Quick Selectors by Keyword: ' + ', '.join([f'{k}: {", ".join(v[:3])}' for k, v in ids_with_keywords.items()]) if ids_with_keywords else ''}

{'📝 Text Previews: ' + '\n'.join([f"  • #{el_id}: {preview}" for el_id, preview in list(text_previews.items())[:5]]) if text_previews else ''}

{'📋 Available Routes: ' + ', '.join(set(available_routes)) if available_routes else '📋 React Admin Routes: /posts, /comments, /tags, /users, /'}

{walkthrough_info}

🧠 Your Capabilities:
  • You have full access to MCP tools for Abaqus workflows
  • You can see what the user sees on the page
  • You can reference specific UI elements by their IDs
  • You can help users navigate and complete tasks
  • You can trigger UI actions automatically when users ask

💡 CRITICAL: Navigation & Highlighting Instructions:
  
  When users request navigation, highlighting, or to see a section, you MUST:
  1. Respond naturally and conversationally
  2. IMMEDIATELY take action - don't just describe what you would do, actually do it
  3. ALWAYS include an [ACTIONS] block at the END of your response (this is hidden from users)
  
  Action Format (REQUIRED for navigation/highlighting):
  [ACTIONS]
  {{
    "navigate": "/path",
    "highlight": ["selector1", "selector2"]
  }}
  [/ACTIONS]
  
  Navigation Rules (React Admin):
  • "tags" → navigate to "/tags" AND highlight element with "tags" in ID or text
  • "comments" → navigate to "/comments" AND highlight element with "comments" in ID or text  
  • "posts" → navigate to "/posts" AND highlight element with "posts" in ID or text
  • "users" → navigate to "/users" AND highlight element with "users" in ID or text
  • "search" → highlight the search input field (look for input with placeholder "Search")
  • Look at the "Available Element IDs" and "Quick Selectors by Keyword" lists above to find matching selectors
  • IMPORTANT: If user is on a different page (e.g., /posts) and asks for "comments", you MUST navigate to /comments first
  
  Highlighting Rules:
  • Use CSS selectors: "#element-id", ".class-name", "tag-name"
  • Use component queries: text content like "comments", "tags", "features"
  • Try multiple selectors: ["#comments", "comments", ".comment-section"]
  • When user says "highlight X", immediately highlight it - don't ask, just do it
  • When user asks to READ, COPY, or TELL what the page says (e.g., "what does it say", "copy text", "read this"), locate the relevant element (e.g., #react-admin-title, #main-content), quote the text back verbatim, and optionally highlight afterwards. Use the Text Previews above to find the right element quickly.
  
  EXAMPLES (you MUST follow this format EXACTLY):
  
  User: "highlight Comments"
  Your response MUST be: "I'll highlight the comments section for you!" [ACTIONS]{{"highlight": ["#comments", "comments", ".comment-section"]}}[/ACTIONS]
  
  User: "tags"
  Your response MUST be: "Let me show you the tags section." [ACTIONS]{{"navigate": "/tags", "highlight": ["#tags", "tags"]}}[/ACTIONS]
  
  User: "go to posts"
  Your response MUST be: "I'll take you to the posts page!" [ACTIONS]{{"navigate": "/posts", "highlight": ["#posts", "posts"]}}[/ACTIONS]
  
  User: "comments pls highlight"
  If on /posts page: Your response MUST be: "I'll take you to the comments page!" [ACTIONS]{{"navigate": "/comments", "highlight": ["comments"]}}[/ACTIONS]
  If on /comments page: Your response MUST be: "I'll highlight the comments section for you!" [ACTIONS]{{"highlight": ["comments", "comment"]}}[/ACTIONS]
  
  User: "highlight comments" (when on /posts page)
  Your response MUST be: "I'll navigate to the comments page and highlight it for you!" [ACTIONS]{{"navigate": "/comments", "highlight": ["comments"]}}[/ACTIONS]
  
  User: "locate pls"
  Your response MUST be: "Let me locate that for you!" [ACTIONS]{{"highlight": ["#search", "search", "input"]}}[/ACTIONS]

  User: "tell me here what it says"
  Your response MUST be: "Here's what I see: \"<quote the visible text from the appropriate element>\"". After quoting, you MAY add [ACTIONS]{{"highlight": ["#main-content"]}}[/ACTIONS] if highlighting helps.
  
  IMPORTANT: 
  - The [ACTIONS] block is AUTOMATICALLY REMOVED from what users see
  - If user asks for navigation/highlighting, you MUST include [ACTIONS] - no exceptions
  - Take action immediately, don't just describe - actually navigate and highlight
  - Match user requests to available routes and elements from the context above

💡 General Instructions:
  • Write in a natural, conversational, and friendly tone - like you're helping a friend
  • Be helpful and personable - avoid robotic or overly formal language
  • Use contractions, casual phrases, and warm expressions when appropriate
  • Keep responses concise but not terse - explain what you're doing
  • Reference visible elements when relevant (e.g., "Click the #submit-button")
  • Use tools when needed to answer questions or generate files
  • If the user is in a walkthrough, help them complete the current step
  
  ⚠️ CRITICAL ACTION RULES:
  • When user asks to "highlight", "show", "go to", "navigate to", or mentions a section name (tags, comments, posts, users, etc.)
  • You MUST include an [ACTIONS] block with navigate and/or highlight
  • Don't just describe - actually perform the action
  • Look at the Interactive Elements list above to find matching selectors
  • React Admin routes: /posts, /comments, /tags, /users, /, etc.
  • If user says one word like "tags" or "comments", they want to see/highlight that section

═══════════════════════════════════════════════════════════════
    """.strip()
    
    return system_context


def format_history_for_agent(history: List[Message]) -> List[Dict[str, Any]]:
    """Convert TaskMapr message history to OpenAI format."""
    formatted = []
    for msg in history[-50:]:  # Last 50 messages to avoid token overload
        formatted.append({
            "role": msg.role,
            "content": msg.content,
        })
    return formatted


# ────────────────────────────────────────────────────────────────────────────────
# Endpoint Handler
# ────────────────────────────────────────────────────────────────────────────────

def create_taskmapr_endpoint(
    authenticate_supabase_user,
    ensure_session_row,
    make_sqlalchemy_session,
    make_run_config,
    orchestrator_agent,
    Runner,
):
    """
    Factory function to create the TaskMapr orchestration endpoint.
    This allows us to inject dependencies from the main server module.
    """
    
    async def taskmapr_orchestrate(
        request: Request,
        context: AgentContextPackage,
        authorization: Optional[str] = Header(None),
    ):
        """
        TaskMapr Orchestrator Endpoint - Streaming agent responses with rich context.
        
        This endpoint:
        1. Receives comprehensive context from TaskMapr (prompt, history, DOM elements, page state)
        2. Enriches the agent's system prompt with page awareness
        3. Streams the agent's response back with typed events
        4. Maintains conversation history in the database
        
        Request Body: AgentContextPackage
        Response: Server-Sent Events (SSE) stream
        
        Events:
        - text_delta: Streaming text chunks
        - reasoning_start/done: Reasoning blocks
        - reasoning_delta: Reasoning text chunks
        - tool_call_started/completed: Tool execution notifications
        - actions: Actions for TaskMapr UI to execute
        - error: Error messages
        - complete: Stream finished
        """
        # Authenticate user
        auth = authenticate_supabase_user(authorization)
        user_id = auth.user_id
        
        # Use sessionId from context or generate one
        session_key = context.sessionId or f"taskmapr_{user_id}_{datetime.now().timestamp()}"
        
        await ensure_session_row(session_key, user_id)
        
        # Setup session persistence
        session = make_sqlalchemy_session(session_key)
        if session is None:
            print("Warning: continuing without session persistence")
        
        run_cfg = make_run_config(session_key, user_id)
        
        # Build enhanced system context
        system_context = build_taskmapr_system_context(context)
        
        # Format history
        formatted_history = format_history_for_agent(context.history)
        
        # Combine system context + history + current prompt
        # The prompt needs to be injected with the system context
        enhanced_prompt = f"{system_context}\n\nUser request: {context.prompt}\n\nRemember: If the user asks to navigate, highlight, or show something, you MUST include an [ACTIONS] block at the end of your response!"
        
        # Initialize streaming
        try:
            print(f"[TaskMapr] Starting stream for session {session_key}")
            print(f"[TaskMapr] Page: {context.pageContext.pathname}")
            print(f"[TaskMapr] Interactive elements: {len([e for e in context.domElements if e.isInteractive])}")
            
            streamed = Runner.run_streamed(
                orchestrator_agent,
                input=enhanced_prompt,
                session=session,
                run_config=run_cfg,
                max_turns=24,
            )
        except Exception as exc:
            async def error_gen():
                err_payload = json.dumps({
                    "event": "error", 
                    "data": {"message": str(exc) or "Stream initialization failed"}
                })
                yield {"data": err_payload}
            print(f"[TaskMapr] Stream initialization error: {exc}")
            return EventSourceResponse(error_gen(), media_type="text/event-stream")
        
        # Stream generator
        async def gen():
            disconnected = False
            reasoning_started = False
            streamed_item_ids: set[str] = set()
            emitted_message_ids: set[str] = set()
            collected_tool_calls: List[Dict[str, str]] = []
            
            def emit_event(event_type: str, data: Dict[str, Any]):
                return {"data": json.dumps({"event": event_type, "data": data})}
            
            def emit_text_delta(text: str):
                if text:
                    return emit_event("text_delta", {"text": text})
                return None
            
            def emit_reasoning_delta(text: str):
                if text:
                    return emit_event("reasoning_delta", {"text": text})
                return None
            
            def emit_reasoning_start():
                return emit_event("reasoning_start", {})
            
            def emit_reasoning_done():
                return emit_event("reasoning_done", {})
            
            def emit_error(message: str):
                return emit_event("error", {"message": message})
            
            def emit_actions(actions: List[AgentAction]):
                """Emit actions for TaskMapr UI to execute."""
                return emit_event("actions", {
                    "actions": [a.dict() for a in actions]
                })
            
            def emit_metadata(metadata: Dict[str, Any]):
                """Emit metadata about the response."""
                return emit_event("metadata", metadata)
            
            def extract_message_text(message_item):
                text_fragments = []
                for content in getattr(message_item, "content", []) or []:
                    content_type = getattr(content, "type", "")
                    if content_type == "output_text":
                        fragment = getattr(content, "text", "")
                        if fragment:
                            text_fragments.append(fragment)
                    elif content_type == "output_refusal":
                        fragment = getattr(content, "refusal", "")
                        if fragment:
                            text_fragments.append(fragment)
                return "".join(text_fragments)
            
            # Track full response text for action extraction
            full_response_text = ""
            
            def extract_actions_from_response(text: str, context: AgentContextPackage) -> tuple[str, List[AgentAction]]:
                """Extract actions from agent response using [ACTIONS] JSON block and return cleaned text."""
                actions: List[AgentAction] = []
                cleaned_text = text
                
                import re
                import json
                
                # Look for [ACTIONS]...[/ACTIONS] block (case-insensitive, multiline)
                actions_block_pattern = r'\[ACTIONS\](.*?)\[/ACTIONS\]'
                match = re.search(actions_block_pattern, text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    print(f"[TaskMapr] Found [ACTIONS] block in response")
                    actions_content = match.group(1).strip()
                    print(f"[TaskMapr] Actions content: {actions_content[:200]}")
                    
                    # Remove the actions block from the text
                    cleaned_text = re.sub(actions_block_pattern, '', text, flags=re.DOTALL | re.IGNORECASE).strip()
                    
                    try:
                        actions_json = json.loads(actions_content)
                        print(f"[TaskMapr] Parsed actions JSON: {actions_json}")
                        
                        # Extract navigate action
                        if "navigate" in actions_json and actions_json["navigate"]:
                            actions.append(AgentAction(
                                type="navigate",
                                payload={"path": str(actions_json["navigate"])}
                            ))
                            print(f"[TaskMapr] Added navigate action: {actions_json['navigate']}")
                        
                        # Extract highlight action
                        if "highlight" in actions_json and actions_json["highlight"]:
                            selectors = actions_json["highlight"]
                            if isinstance(selectors, str):
                                selectors = [selectors]
                            elif not isinstance(selectors, list):
                                selectors = []
                            
                            if selectors:
                                actions.append(AgentAction(
                                    type="highlight",
                                    payload={"selectors": selectors, "duration": 5000}
                                ))
                                print(f"[TaskMapr] Added highlight action with selectors: {selectors}")
                    except json.JSONDecodeError as e:
                        print(f"[TaskMapr] Failed to parse actions JSON: {e}")
                        print(f"[TaskMapr] Raw actions content was: {actions_content}")
                else:
                    print(f"[TaskMapr] No [ACTIONS] block found in response")
                    print(f"[TaskMapr] Response text (last 500 chars): {text[-500:]}")
                
                return cleaned_text, actions
            
            try:
                events_iter = streamed.stream_events().__aiter__()
                heartbeat_interval = 15  # seconds
                
                def emit_heartbeat():
                    return emit_event("heartbeat", {})
                
                while True:
                    # Check for client disconnect
                    if await request.is_disconnected():
                        disconnected = True
                        print(f"[TaskMapr] Client disconnected for session {session_key}")
                        break
                    
                    # Wait for next event with timeout (for heartbeat)
                    try:
                        ev = await asyncio.wait_for(
                            events_iter.__anext__(), 
                            timeout=heartbeat_interval
                        )
                    except asyncio.TimeoutError:
                        payload = emit_heartbeat()
                        if payload:
                            yield payload
                        continue
                    except StopAsyncIteration:
                        print(f"[TaskMapr] Stream completed for session {session_key}")
                        break
                    
                    try:
                        event_type = getattr(ev, "type", "")
                        
                        # Raw response events (text deltas, reasoning, etc.)
                        if event_type == "raw_response_event":
                            data = getattr(ev, "data", None)
                            if data:
                                data_type = getattr(data, "type", "")
                                
                                # Text content deltas
                                if data_type == "response.output_text.delta":
                                    item_id = getattr(data, "item_id", None)
                                    if isinstance(item_id, str):
                                        streamed_item_ids.add(item_id)
                                    delta_text = getattr(data, "delta", "")
                                    full_response_text += delta_text
                                    
                                    # Check if we've started receiving an [ACTIONS] block
                                    # If so, don't stream that part to the user
                                    import re
                                    # Check if delta contains start of [ACTIONS] block
                                    if "[ACTIONS]" in (full_response_text[-100:] if len(full_response_text) > 100 else full_response_text):
                                        # We might be in an actions block, check if we should skip this delta
                                        # For now, still send it but we'll clean it at the end
                                        # A better approach would be to buffer and detect, but for simplicity
                                        # we'll just send everything and clean at the end
                                        pass
                                    
                                    payload = emit_text_delta(delta_text)
                                    if payload:
                                        yield payload
                                
                                # Reasoning deltas
                                elif data_type in {
                                    "response.reasoning_text.delta",
                                    "response.reasoning_summary_text.delta",
                                }:
                                    if not reasoning_started:
                                        yield emit_reasoning_start()
                                        reasoning_started = True
                                    payload = emit_reasoning_delta(getattr(data, "delta", ""))
                                    if payload:
                                        yield payload
                                
                                # Reasoning done markers
                                elif data_type in {
                                    "response.reasoning_text.done",
                                    "response.reasoning_summary_text.done",
                                }:
                                    if reasoning_started:
                                        yield emit_reasoning_done()
                                        reasoning_started = False
                                
                                # Completed message payloads (non-streaming models)
                                elif data_type in {
                                    "response.output_item.added",
                                    "response.output_item.done",
                                }:
                                    message_item = getattr(data, "item", None)
                                    message_id = getattr(message_item, "id", None)
                                    if getattr(message_item, "type", None) == "message":
                                        if isinstance(message_id, str):
                                            if message_id in emitted_message_ids:
                                                continue
                                            emitted_message_ids.add(message_id)
                                            if message_id in streamed_item_ids:
                                                continue
                                        text = extract_message_text(message_item)
                                        full_response_text += text
                                        payload = emit_text_delta(text)
                                        if payload:
                                            yield payload
                                
                                # Error events
                                elif data_type == "response.failed":
                                    response_obj = getattr(data, "response", None)
                                    err_message = "Response failed"
                                    if response_obj is not None:
                                        err = getattr(response_obj, "error", None)
                                        message = getattr(err, "message", None) if err else None
                                        if message:
                                            err_message = message
                                    yield emit_error(err_message)
                                
                                elif data_type in {"error", "response.error"}:
                                    err_message = getattr(data, "message", None) or "Stream error"
                                    yield emit_error(err_message)
                        
                        # Tool call events
                        elif event_type == "run_item_stream_event":
                            name = getattr(ev, "name", "")
                            if name == "tool_called":
                                raw_tool_item = getattr(ev, "item", None)
                                raw_tool = getattr(raw_tool_item, "raw_item", None)
                                tool_name = None
                                if isinstance(raw_tool, dict):
                                    tool_name = raw_tool.get("name") or raw_tool.get("tool_name")
                                else:
                                    tool_name = getattr(raw_tool, "name", None) or getattr(raw_tool, "tool_name", None)
                                if not tool_name:
                                    tool_name = "unknown"
                                collected_tool_calls.append({"tool_name": tool_name, "status": "started"})
                                yield emit_event("tool_call_started", {"tool_name": tool_name})
                            elif name == "tool_output":
                                raw_tool_item = getattr(ev, "item", None)
                                raw_tool = getattr(raw_tool_item, "raw_item", None)
                                tool_name = None
                                if isinstance(raw_tool, dict):
                                    tool_name = raw_tool.get("name") or raw_tool.get("tool_name")
                                else:
                                    tool_name = getattr(raw_tool, "name", None) or getattr(raw_tool, "tool_name", None)
                                if not tool_name:
                                    tool_name = "unknown"
                                yield emit_event("tool_call_completed", {"tool_name": tool_name})
                        
                        elif event_type == "agent_updated_stream_event":
                            reasoning_started = False
                    
                    except Exception as e:
                        # Never let the stream crash on event-shape quirks
                        print(f"[TaskMapr] Stream event error: {e}")
                
            except Exception as e:
                print(f"[TaskMapr] Streaming failure: {e}")
                yield emit_error(str(e) or "Unknown streaming error")
            
            # Cleanup
            if reasoning_started:
                yield emit_reasoning_done()
            
            # Extract actions and clean response text
            cleaned_response_text = full_response_text
            extracted_actions = []
            if full_response_text:
                cleaned_response_text, extracted_actions = extract_actions_from_response(full_response_text, context)
                if extracted_actions:
                    print(f"[TaskMapr] Extracted {len(extracted_actions)} actions from response")
                    payload = emit_actions(extracted_actions)
                    if payload:
                        yield payload
            
            # Note: The cleaned response text (without [ACTIONS] block) is already in full_response_text
            # and has been streamed to the client. The actions block is removed automatically.
            
            # Emit final metadata
            if collected_tool_calls:
                yield emit_metadata({
                    "tools_used": collected_tool_calls,
                    "page_context": context.pageContext.dict(),
                })
            
            if not disconnected:
                yield emit_event("complete", {"sessionId": session_key})
        
        return EventSourceResponse(gen(), media_type="text/event-stream")
    
    return taskmapr_orchestrate
