import argparse
import json

from dotenv import load_dotenv

from src.config import settings
from src.core.app import build_orchestrator
from src.core.task import Task
from src.tools.database import DBTool


def parse_metadata(values):
    metadata = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"Invalid metadata value '{value}'. Use key=value.")
        key, raw = value.split("=", 1)
        metadata[key] = raw
    return metadata


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="ArkAgents AI Business Manager command line interface"
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a business automation task")
    run_parser.add_argument("description", help="Task description")
    run_parser.add_argument("--agent", help="Force a specific agent")
    run_parser.add_argument("--meta", action="append", default=[], help="Task metadata as key=value")
    run_parser.add_argument("--allow-db-writes", action="store_true", help="Allow insert/update/delete SQL")
    run_parser.add_argument("--use-llm", action="store_true", help="Enable configured LLM providers for planning")

    subparsers.add_parser("agents", help="List registered agents")
    subparsers.add_parser("seed-db", help="Create demo customer data")
    ui_parser = subparsers.add_parser("ui", help="Run the browser admin console")
    ui_parser.add_argument("--host", default="127.0.0.1")
    ui_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    command = args.command or "agents"

    if command == "ui":
        from src.web.server import run

        run(host=args.host, port=args.port)
        return

    if command == "seed-db":
        result = DBTool(settings.DB_PATH, allow_writes=True).seed_demo_data()
        print(json.dumps(result, indent=2))
        return

    orchestrator = build_orchestrator(
        allow_db_writes=getattr(args, "allow_db_writes", False),
        use_llm=getattr(args, "use_llm", False),
    )

    if command == "agents":
        print(json.dumps(orchestrator.manager.registry.describe_agents(), indent=2))
        return

    metadata = parse_metadata(args.meta)
    task = Task(description=args.description, agent=args.agent, metadata=metadata)
    result = orchestrator.run(task)
    print(json.dumps(result.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
