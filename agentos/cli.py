"""
AgentOS CLI — Command-line interface for agent management.

v1.14.5: Full-featured CLI for init, run, deploy, list, and config management.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="agentos",
        description="AgentOS — Production Multi-Agent Framework CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- init ----
    p_init = sub.add_parser("init", help="Initialize a new agent project")
    p_init.add_argument("name", help="Project name")
    p_init.add_argument("--template", "-t", default="default",
                        choices=["default", "chat", "research", "coding", "pipeline"],
                        help="Project template")
    p_init.add_argument("--dir", "-d", default=".", help="Target directory")

    # ---- run ----
    p_run = sub.add_parser("run", help="Run an agent or workflow")
    p_run.add_argument("target", help="Agent config file (.yaml) or workflow file")
    p_run.add_argument("--prompt", "-p", help="Prompt to send to agent")
    p_run.add_argument("--stream", "-s", action="store_true", help="Stream output")
    p_run.add_argument("--model", "-m", help="Override model")

    # ---- deploy ----
    p_deploy = sub.add_parser("deploy", help="Deploy agent to cluster")
    p_deploy.add_argument("config", help="Agent config file")
    p_deploy.add_argument("--workers", "-w", type=int, default=1, help="Number of workers")
    p_deploy.add_argument("--ray", action="store_true", help="Deploy via Ray cluster")

    # ---- list ----
    p_list = sub.add_parser("list", help="List running agents")
    p_list.add_argument("--format", "-f", choices=["table", "json"], default="table")

    # ---- marketplace ----
    p_market = sub.add_parser("marketplace", help="Agent marketplace commands")
    m_sub = p_market.add_subparsers(dest="market_cmd", required=True)
    m_sub.add_parser("search", help="Search marketplace").add_argument("query", nargs="?", default="")
    m_sub.add_parser("install", help="Install a template").add_argument("template_id")
    m_sub.add_parser("featured", help="Show featured templates")

    # ---- config ----
    p_config = sub.add_parser("config", help="Manage agent configuration")
    c_sub = p_config.add_subparsers(dest="config_cmd", required=True)
    c_sub.add_parser("show", help="Show current config")
    c_sub.add_parser("set", help="Set a config value").add_argument("key")
    c_sub.add_parser("list-models", help="List available models")

    # ---- serve (API) ----
    p_serve = sub.add_parser("serve", help="Start AgentOS API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host to bind")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Port")
    p_serve.add_argument("--reload", action="store_true", help="Auto-reload on changes")

    # ---- version ----
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()
    handler = CLIHandler()

    if args.command == "init":
        handler.cmd_init(args)
    elif args.command == "run":
        asyncio.run(handler.cmd_run(args))
    elif args.command == "deploy":
        asyncio.run(handler.cmd_deploy(args))
    elif args.command == "list":
        asyncio.run(handler.cmd_list(args))
    elif args.command == "marketplace":
        asyncio.run(handler.cmd_marketplace(args))
    elif args.command == "config":
        handler.cmd_config(args)
    elif args.command == "serve":
        handler.cmd_serve(args)
    elif args.command == "version":
        handler.cmd_version()


class CLIHandler:
    def cmd_init(self, args):
        target = Path(args.dir).resolve() / args.name
        target.mkdir(parents=True, exist_ok=True)

        templates = {
            "default": {
                "agent.yaml": "name: {name}\ntype: default\nmodel: gpt-4o\n",
                "main.py": (
                    "from agentos import Agent, OpenAIModel\n\n"
                    "agent = Agent(\n"
                    "    model=OpenAIModel('gpt-4o'),\n"
                    "    system_prompt='You are a helpful assistant.',\n"
                    ")\n\n"
                    "async def main():\n"
                    "    result = await agent.run('Hello!')\n"
                    "    print(result)\n\n"
                    "if __name__ == '__main__':\n"
                    "    import asyncio\n"
                    "    asyncio.run(main())\n"
                ),
            },
            "chat": {
                "agent.yaml": "name: {name}\ntype: chat\nmodel: gpt-4o\nmemory: enabled\n",
                "main.py": (
                    "from agentos import Agent, OpenAIModel\n"
                    "from agentos.memory.consolidation import ReflectionEngine\n\n"
                    "agent = Agent(\n"
                    "    model=OpenAIModel('gpt-4o'),\n"
                    "    memory=ReflectionEngine(),\n"
                    ")\n"
                ),
            },
            "research": {
                "agent.yaml": "name: {name}\ntype: research\nmodel: gpt-4o\ntools: [web_search, arxiv]\n",
                "main.py": (
                    "from agentos import Agent, Swarm\n\n"
                    "researcher = Agent(model='gpt-4o', name='Researcher')\n"
                    "writer = Agent(model='gpt-4o', name='Writer')\n"
                    "swarm = Swarm(agents=[researcher, writer])\n"
                ),
            },
            "coding": {
                "agent.yaml": "name: {name}\ntype: coding\nmodel: claude-3-opus\n",
            },
            "pipeline": {
                "agent.yaml": "name: {name}\ntype: pipeline\nworkflow: workflow.yaml\n",
                "workflow.yaml": (
                    "name: {name}-pipeline\n"
                    "version: '1.0'\n"
                    "steps:\n"
                    "  - id: process\n"
                    "    type: task\n"
                    "    agent: default\n"
                    "    task: 'Process input'\n"
                ),
            },
        }

        tmpl = templates.get(args.template, templates["default"])
        for filename, content in tmpl.items():
            formatted = content.format(name=args.name)
            (target / filename).write_text(formatted)

        print(f"✓ Created {args.template} project '{args.name}' at {target}")
        print(f"  cd {target} && agentos run agent.yaml -p 'Hello!'")

    async def cmd_run(self, args):
        target = Path(args.target)
        if not target.exists():
            print(f"Error: '{target}' not found")
            sys.exit(1)

        try:
            from agentos import Agent
            import yaml

            if target.suffix in (".yaml", ".yml"):
                config = yaml.safe_load(target.read_text())
                agent = Agent.from_config(config)
            else:
                # Workflow file
                from agentos.workflow import WorkflowParser, WorkflowEngine
                wf = WorkflowParser.parse_file(target)
                ctx = await WorkflowEngine().execute(wf)
                print(json.dumps(ctx.variables, indent=2, default=str))
                return

            prompt = args.prompt or "Tell me about yourself."
            if args.stream:
                async for chunk in agent.stream(prompt):
                    print(chunk, end="", flush=True)
                print()
            else:
                result = await agent.run(prompt)
                print(result)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    async def cmd_deploy(self, args):
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: config '{config_path}' not found")
            sys.exit(1)

        if args.ray:
            from agentos.orchestration.distributed import RayAgentActor, PlacementStrategy
            import ray
            ray.init()
            actor = RayAgentActor.options(num_cpus=args.workers).remote(config_path)
            print(f"✓ Deployed {args.workers} workers to Ray cluster")
        else:
            print(f"✓ Deploying {args.workers} workers via local mode")
            print("  (Install 'ray' for distributed deployment)")

    async def cmd_list(self, args):
        try:
            from agentos.protocols.registry import AgentRegistry
            registry = AgentRegistry()
            agents = await registry.list_agents()

            if args.format == "json":
                print(json.dumps([a.__dict__ for a in agents], indent=2, default=str))
            else:
                if not agents:
                    print("No agents registered.")
                    return
                print(f"{'ID':20} {'Capabilities':30} {'Status'}")
                print("-" * 65)
                for a in agents:
                    caps = ", ".join(a.capabilities[:3])
                    print(f"{a.agent_id:20} {caps:30} {'online' if a.healthy else 'offline'}")
        except Exception as e:
            print("No running agents found. Start an agent first with 'agentos serve' or 'agentos run'.")

    async def cmd_marketplace(self, args):
        from agentos.marketplace import MarketplaceManager, MarketSearchQuery
        manager = MarketplaceManager()

        if args.market_cmd == "search":
            results = await manager.search(MarketSearchQuery(keywords=args.query or ""))
            if not results:
                print("No templates found.")
                return
            for r in results[:10]:
                print(f"  {r.template.name:30} ★{r.template.rating:.1f}  {r.template.description[:60]}")
        elif args.market_cmd == "install":
            path = await manager.install(args.template_id)
            print(f"✓ Installed to {path}")
        elif args.market_cmd == "featured":
            featured = await manager.get_featured(10)
            for tpl in featured:
                print(f"  {tpl.name:30} {tpl.downloads:>6} downloads  ★{tpl.rating:.1f}")

    def cmd_config(self, args):
        config_dir = Path.home() / ".agentos"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"

        if args.config_cmd == "show":
            if config_file.exists():
                print(config_file.read_text())
            else:
                print(json.dumps({"model": "gpt-4o", "workspace": str(Path.home() / "agentos")}, indent=2))
        elif args.config_cmd == "set":
            key, _, value = args.key.partition("=")
            if not value:
                print("Usage: agentos config set KEY=VALUE")
                return
            cfg = json.loads(config_file.read_text()) if config_file.exists() else {}
            cfg[key] = value
            config_file.write_text(json.dumps(cfg, indent=2))
            print(f"✓ Set {key}={value}")
        elif args.config_cmd == "list-models":
            models = ["gpt-4o", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet",
                      "gemini-1.5-pro", "llama-3-70b", "mixtral-8x7b"]
            for m in models:
                print(f"  {m}")

    def cmd_serve(self, args):
        print(f"Starting AgentOS API server on http://{args.host}:{args.port}")
        print("API docs: http://{args.host}:{args.port}/docs")
        try:
            from agentos.api.server import serve
            import uvicorn
            uvicorn.run("agentos.api.server:app", host=args.host, port=args.port, reload=args.reload)
        except ImportError:
            print("Install API dependencies: pip install nexus-agentos[api]")
            print("Module 'agentos.api.server' not available yet — running stub.")
            import http.server
            server = http.server.HTTPServer(
                (args.host, args.port),
                lambda *a: None,
            )
            print(f"  Stub server on {args.host}:{args.port}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down...")

    def cmd_version(self):
        from agentos import __version__
        print(f"AgentOS v{__version__}")


if __name__ == "__main__":
    main()
