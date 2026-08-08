from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from src.config import settings
from src.core.app import build_orchestrator
from src.core.task import Task
from src.tools.database import DBTool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"

TASK_HISTORY: List[Dict[str, Any]] = []


def add_to_history(task_result: Dict[str, Any]) -> None:
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "description": task_result.get("description", ""),
        "agent": task_result.get("agent", "auto"),
        "status": task_result.get("status", "unknown"),
        "result_summary": str(task_result.get("result", {}))[:200],
    }
    TASK_HISTORY.insert(0, entry)
    if len(TASK_HISTORY) > 100:
        TASK_HISTORY.pop()


class ArkAgentsWebHandler(BaseHTTPRequestHandler):
    server_version = "ArkAgentsWeb/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self.write_json({
                "status": "ok",
                "project": "ArkAgents",
                "llm_enabled_by_default": settings.ENABLE_LLM,
            })
            return

        if parsed.path == "/api/agents":
            orchestrator = build_orchestrator(use_llm=False)
            self.write_json(orchestrator.manager.registry.describe_agents())
            return

        if parsed.path == "/api/schema":
            query = parse_qs(parsed.query)
            db_path = query.get("db_path", [settings.DB_PATH])[0] or settings.DB_PATH
            try:
                self.write_json({"schema": DBTool(db_path).describe_schema()})
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return

        if parsed.path == "/api/history":
            self.write_json({"history": TASK_HISTORY[:50]})
            return

        if parsed.path == "/api/ws":
            self.handle_websocket()
            return

        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self.read_json()

        if parsed.path == "/api/seed-db":
            db_path = payload.get("db_path") or settings.DB_PATH
            try:
                result = DBTool(db_path, allow_writes=True).seed_demo_data()
                self.write_json(result)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return

        if parsed.path == "/api/run":
            self.run_task(payload)
            return

        if parsed.path == "/api/templates":
            from src.agents.workers.email_agent import EmailAgent
            agent = EmailAgent()
            self.write_json(agent.list_templates())
            return

        self.write_json({"error": "Endpoint not found"}, status=404)

    def run_task(self, payload: Dict[str, Any]) -> None:
        description = str(payload.get("description") or "").strip()
        if not description:
            self.write_json({"error": "Task description is required"}, status=400)
            return

        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        db_path = payload.get("db_path") or settings.DB_PATH
        agent = payload.get("agent") or None
        use_llm = bool(payload.get("use_llm", False))
        allow_db_writes = bool(payload.get("allow_db_writes", False))

        try:
            orchestrator = build_orchestrator(
                db_path=db_path,
                allow_db_writes=allow_db_writes,
                use_llm=use_llm,
            )
            result = orchestrator.run(Task(description=description, agent=agent, metadata=metadata))
            result_dict = result.to_dict()
            add_to_history(result_dict)
            asyncio.create_task(broadcast_ws({"type": "task_complete", "result": result_dict}))
            self.write_json(result_dict)
        except Exception as exc:
            self.write_json({"error": str(exc)}, status=500)

    def serve_static(self, request_path: str) -> None:
        relative_path = request_path.strip("/") or "index.html"
        file_path = (WEB_ROOT / relative_path).resolve()

        if WEB_ROOT.resolve() not in file_path.parents and file_path != WEB_ROOT.resolve():
            self.write_json({"error": "Invalid path"}, status=400)
            return

        if not file_path.exists() or file_path.is_dir():
            self.write_json({"error": "File not found"}, status=404)
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def write_json(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    load_dotenv()
    server = ThreadingHTTPServer((host, port), ArkAgentsWebHandler)
    print(f"ArkAgents UI running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ArkAgents web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()