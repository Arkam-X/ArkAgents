from dotenv import load_dotenv

load_dotenv()

from src.core.agent_registry import AgentRegistry
from src.llm.router import LLMRouter

# Agents
from src.agents.manager.manager_agent import ManagerAgent
from src.agents.workers.db_agent import DBAgent

# Tools
from src.tools.database.db_tools import DBTool

# Orchestration
from src.core.orchestrator import Orchestrator
from src.core.task import Task

from src.workflows.workflow_engine import WorkflowEngine



def main():
    print("🚀 Starting ARKAGENTS...")

    # Initialize infrastructure
    llm_router = LLMRouter()
    db_tool = DBTool()

    # Initialize agents
    db_agent = DBAgent(db_tool=db_tool, llm=llm_router)
    registry = AgentRegistry()
    registry.register("db", db_agent)

    manager = ManagerAgent(registry=registry, llm=llm_router)
    orchestrator = Orchestrator(manager)
    workflow = WorkflowEngine(manager)

    # Workflow task example
    task = Task(description="Fetch users from DB", agent="db")

    orchestrator_result = orchestrator.run(task)
    print("Orchestrator Result:", orchestrator_result.to_dict())

    # Manager-level orchestration
    manager_task = Task(description="Process user data", agent="db")
    manager_result = manager.run(manager_task)
    print("Manager Result:", manager_result)

    # Workflow example
    # tasks = [
    #     Task(description="Fetch leads", agent="db"),
    #     Task(description="Save leads to database", agent="db")
    # ]
    tasks = Task(
        description="Get all users from database"
    )

    workflow_results = workflow.run(tasks)
    for r in workflow_results:
        print("Workflow task result:", r.to_dict())

    print("\n📊 Final Result:\n", manager_result)


if __name__ == "__main__":
    main()