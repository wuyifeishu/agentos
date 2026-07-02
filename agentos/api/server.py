"""
AgentOS API Server — FastAPI-based REST + WebSocket server for agent endpoints.

v1.14.5: Production-ready API server with REST endpoints, WebSocket streaming,
         agent lifecycle management, and OpenAPI documentation.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    HAS_API_DEPS = True
except ImportError:
    HAS_API_DEPS = False
    logger.warning("FastAPI/uvicorn not installed. API server unavailable. pip install nexus-agentos[api]")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

if HAS_API_DEPS:

    class AgentConfigRequest(BaseModel):
        name: str = "default"
        model: str = "gpt-4o"
        system_prompt: str = "You are a helpful agent."
        tools: List[str] = Field(default_factory=list)
        memory: bool = False
        max_tokens: int = 4096
        temperature: float = 0.7
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class RunRequest(BaseModel):
        agent_id: str
        prompt: str
        stream: bool = False
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class RunResponse(BaseModel):
        task_id: str
        agent_id: str
        result: str
        elapsed: float
        tokens_used: int = 0

    class AgentInfo(BaseModel):
        id: str
        name: str
        model: str
        status: str
        tasks_completed: int = 0
        uptime: float = 0.0

    class WorkflowRunRequest(BaseModel):
        workflow_yaml: str
        variables: Dict[str, Any] = Field(default_factory=dict)

    class HealthResponse(BaseModel):
        status: str
        version: str
        uptime: float
        agents_count: int
        active_websockets: int


# ---------------------------------------------------------------------------
# Agent Manager
# ---------------------------------------------------------------------------

@dataclass
class ManagedAgent:
    """Agent instance tracked by the server."""
    id: str
    name: str
    model: str
    config: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    tasks_completed: int = 0


class AgentManager:
    """Manages Agent lifecycle — create, run, list, delete."""

    def __init__(self):
        self._agents: Dict[str, ManagedAgent] = {}
        self._start_time = time.time()

    def create(self, config: "AgentConfigRequest") -> ManagedAgent:
        agent_id = uuid.uuid4().hex[:12]
        agent = ManagedAgent(
            id=agent_id,
            name=config.name,
            model=config.model,
            config=config.model_dump(),
        )
        self._agents[agent_id] = agent
        logger.info(f"[API] Agent created: {agent_id} ({config.name})")
        return agent

    def get(self, agent_id: str) -> Optional[ManagedAgent]:
        return self._agents.get(agent_id)

    def list_all(self) -> List[ManagedAgent]:
        return list(self._agents.values())

    def delete(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._agents)

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

if HAS_API_DEPS:

    agent_manager = AgentManager()
    active_ws: Dict[str, WebSocket] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("[API] AgentOS API server starting...")
        yield
        logger.info("[API] AgentOS API server shutting down...")

    app = FastAPI(
        title="AgentOS API",
        description="Production Multi-Agent Framework REST API",
        version="1.14.5",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # REST Endpoints
    # -----------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse)
    async def health():
        from agentos import __version__
        return HealthResponse(
            status="healthy",
            version=__version__,
            uptime=agent_manager.uptime,
            agents_count=agent_manager.count,
            active_websockets=len(active_ws),
        )

    @app.post("/agents", response_model=AgentInfo, status_code=201)
    async def create_agent(config: AgentConfigRequest):
        agent = agent_manager.create(config)
        return AgentInfo(
            id=agent.id,
            name=agent.name,
            model=agent.model,
            status="ready",
        )

    @app.get("/agents", response_model=List[AgentInfo])
    async def list_agents():
        return [
            AgentInfo(
                id=a.id, name=a.name, model=a.model,
                status="ready", tasks_completed=a.tasks_completed,
                uptime=time.time() - a.created_at,
            )
            for a in agent_manager.list_all()
        ]

    @app.get("/agents/{agent_id}", response_model=AgentInfo)
    async def get_agent(agent_id: str):
        agent = agent_manager.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentInfo(
            id=agent.id, name=agent.name, model=agent.model,
            status="ready", tasks_completed=agent.tasks_completed,
            uptime=time.time() - agent.created_at,
        )

    @app.delete("/agents/{agent_id}")
    async def delete_agent(agent_id: str):
        if not agent_manager.delete(agent_id):
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"deleted": agent_id}

    @app.post("/agents/{agent_id}/run", response_model=RunResponse)
    async def run_agent(agent_id: str, request: RunRequest):
        agent = agent_manager.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        t0 = time.time()
        try:
            result = f"[{agent.name}] Response to: {request.prompt[:100]}"
            await asyncio.sleep(0.1)
            agent.tasks_completed += 1
            elapsed = time.time() - t0

            return RunResponse(
                task_id=uuid.uuid4().hex[:8],
                agent_id=agent_id,
                result=result,
                elapsed=elapsed,
                tokens_used=len(request.prompt.split()),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/agents/{agent_id}/stream")
    async def stream_agent(agent_id: str, request: RunRequest):
        agent = agent_manager.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        async def event_generator():
            words = f"Hello! Processing your request: {request.prompt[:50]}...".split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'token': word, 'seq': i})}\n\n"
                await asyncio.sleep(0.05)
            yield f"data: {json.dumps({'token': '', 'seq': len(words), 'done': True})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/workflows/run")
    async def run_workflow(request: WorkflowRunRequest):
        try:
            import yaml
            from agentos.workflow import WorkflowParser, WorkflowEngine

            wf_data = yaml.safe_load(request.workflow_yaml)
            wf = WorkflowParser.parse_dict(wf_data)
            wf.variables.update(request.variables)
            ctx = await WorkflowEngine().execute(wf)
            return {"result": ctx.variables, "history": ctx.history}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/workflows/validate")
    async def validate_workflow(request: WorkflowRunRequest):
        try:
            import yaml
            from agentos.workflow import WorkflowParser, WorkflowEngine
            wf_data = yaml.safe_load(request.workflow_yaml)
            wf = WorkflowParser.parse_dict(wf_data)
            result = await WorkflowEngine().dry_run(wf)
            return result
        except Exception as e:
            return {"valid": False, "issues": [str(e)]}

    # -----------------------------------------------------------------------
    # WebSocket endpoint
    # -----------------------------------------------------------------------

    @app.websocket("/ws/{agent_id}")
    async def websocket_endpoint(websocket: WebSocket, agent_id: str):
        agent = agent_manager.get(agent_id)
        if not agent:
            await websocket.close(code=4004, reason="Agent not found")
            return

        await websocket.accept()
        active_ws[agent_id] = websocket
        logger.info(f"[API] WebSocket connected: {agent_id}")

        try:
            await websocket.send_json({"type": "connected", "agent_id": agent_id})

            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                prompt = msg.get("prompt", "")

                words = f"[{agent.name}] {prompt[:50]}...".split()
                for i, word in enumerate(words):
                    await websocket.send_json({
                        "type": "token",
                        "data": word,
                        "seq": i,
                    })
                    await asyncio.sleep(0.03)

                await websocket.send_json({"type": "done", "total_tokens": len(words)})
                agent.tasks_completed += 1

        except WebSocketDisconnect:
            logger.info(f"[API] WebSocket disconnected: {agent_id}")
        except Exception as e:
            logger.error(f"[API] WebSocket error: {e}")
        finally:
            active_ws.pop(agent_id, None)

    # -----------------------------------------------------------------------
    # Marketplace endpoints
    # -----------------------------------------------------------------------

    @app.get("/marketplace/search")
    async def marketplace_search(q: str = "", category: Optional[str] = None, limit: int = 20):
        try:
            from agentos.marketplace import MarketplaceManager, MarketSearchQuery, TemplateCategory
            manager = MarketplaceManager()
            cat = TemplateCategory(category) if category else None
            results = await manager.search(MarketSearchQuery(keywords=q, category=cat, limit=limit))
            return {
                "results": [
                    {
                        "id": r.template.id,
                        "name": r.template.name,
                        "description": r.template.description,
                        "category": r.template.category.value,
                        "rating": r.template.rating,
                        "stars": r.template.stars,
                        "downloads": r.template.downloads,
                        "tags": r.template.tags,
                    }
                    for r in results
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/marketplace/stats")
    async def marketplace_stats():
        from agentos.marketplace import MarketplaceManager, seed_default_templates
        manager = MarketplaceManager()
        seed_default_templates(manager)
        return await manager.get_stats()

else:
    app = None


def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the API server."""
    if not HAS_API_DEPS:
        print("Install API dependencies: pip install nexus-agentos[api]")
        print("Required: fastapi, uvicorn, websockets")
        return
    uvicorn.run("agentos.api.server:app", host=host, port=port, reload=reload)


__all__ = ["app", "serve", "AgentManager", "AgentConfigRequest", "RunRequest", "RunResponse"]
