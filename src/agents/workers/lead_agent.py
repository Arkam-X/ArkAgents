from typing import Any, Dict, List, Optional
from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class LeadAgent(BaseAgent):
    """Lead extraction worker agent with enrichment, validation, and scoring."""

    def __init__(self, lead_tool=None, llm=None):
        super().__init__(
            name="Lead Agent",
            description="Extracts, enriches, validates, and scores lead contact data",
            tools=[lead_tool] if lead_tool else [],
            llm=llm,
        )
        self.lead_tool = lead_tool

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.lead_tool:
                raise RuntimeError("Lead tool is not configured")

            action = task.metadata.get("action", "extract")
            text = task.metadata.get("text") or task.description
            source = task.metadata.get("source", "manual")
            leads = task.metadata.get("leads", [])

            if action == "extract":
                result = self._handle_extract(text, source)
            elif action == "enrich":
                result = self._handle_enrich(leads)
            elif action == "validate":
                result = self._handle_validate(leads)
            elif action == "score":
                result = self._handle_score(leads)
            elif action == "deduplicate":
                result = self._handle_deduplicate(leads)
            elif action == "export":
                result = self._handle_export(leads, task.metadata)
            else:
                result = {
                    "status": "needs_input",
                    "message": "Provide metadata.action (extract/enrich/validate/score/deduplicate/export) with required parameters.",
                }

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result

    def _handle_extract(self, text: str, source: str) -> Dict[str, Any]:
        leads = self.lead_tool.extract_contacts(text, source=source)
        enriched = self.lead_tool.enrich_leads(leads)
        validated = self.lead_tool.validate_leads(enriched)
        scored = self.lead_tool.score_leads(validated)
        return {"leads": scored, "count": len(scored), "source": source}

    def _handle_enrich(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        enriched = self.lead_tool.enrich_leads(leads)
        return {"leads": enriched, "count": len(enriched)}

    def _handle_validate(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        validated = self.lead_tool.validate_leads(leads)
        return {"leads": validated, "count": len(validated)}

    def _handle_score(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        scored = self.lead_tool.score_leads(leads)
        return {"leads": scored, "count": len(scored)}

    def _handle_deduplicate(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        deduplicated = self.lead_tool.deduplicate_leads(leads)
        return {"leads": deduplicated, "count": len(deduplicated), "removed": len(leads) - len(deduplicated)}

    def _handle_export(self, leads: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        export_format = metadata.get("export_format", "json")
        output_path = metadata.get("output_path", f"leads_export.{export_format}")
        return self.lead_tool.export_leads(leads, export_format, output_path)