import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class ReportTool:
    """Builds comprehensive structured reports from agent results."""

    def summarize(self, items: Iterable[Any]) -> Dict[str, Any]:
        rows: List[Any] = list(items)
        completed = sum(1 for item in rows if self._status(item) == "completed")
        failed = sum(1 for item in rows if self._status(item) == "failed")
        return {
            "total": len(rows),
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / len(rows) * 100, 2) if rows else 0,
            "items": rows,
        }

    def detailed_report(self, items: List[Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        summary = self.summarize(items)
        agents_used = {}
        execution_times = []

        for item in items:
            agent = item.get("agent", "unknown") if isinstance(item, dict) else getattr(item, "agent", "unknown")
            agents_used[agent] = agents_used.get(agent, 0) + 1

            if isinstance(item, dict):
                result = item.get("result", {})
                if isinstance(result, dict):
                    sql = result.get("sql")
                    if sql:
                        execution_times.append({"agent": agent, "query": sql[:100]})

        summary["agents_used"] = agents_used
        summary["execution_details"] = execution_times
        summary["generated_at"] = datetime.now().isoformat()
        summary["metadata"] = metadata
        return summary

    def performance_report(self, items: List[Any]) -> Dict[str, Any]:
        summary = self.summarize(items)
        agent_stats = {}

        for item in items:
            if not isinstance(item, dict):
                continue
            agent = item.get("agent", "unknown")
            status = item.get("status", "unknown")
            error = item.get("error")

            if agent not in agent_stats:
                agent_stats[agent] = {"total": 0, "completed": 0, "failed": 0, "errors": []}

            agent_stats[agent]["total"] += 1
            if status == "completed":
                agent_stats[agent]["completed"] += 1
            elif status == "failed":
                agent_stats[agent]["failed"] += 1
                if error:
                    agent_stats[agent]["errors"].append(error)

        for agent, stats in agent_stats.items():
            stats["success_rate"] = round(stats["completed"] / stats["total"] * 100, 2) if stats["total"] else 0

        summary["agent_performance"] = agent_stats
        return summary

    def agent_performance_report(self, items: List[Any]) -> Dict[str, Any]:
        agent_stats = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            agent = item.get("agent", "unknown")
            status = item.get("status", "unknown")
            result = item.get("result", {})
            duration = result.get("duration_ms") if isinstance(result, dict) else None

            if agent not in agent_stats:
                agent_stats[agent] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "durations": [],
                }

            agent_stats[agent]["total"] += 1
            if status == "completed":
                agent_stats[agent]["completed"] += 1
            elif status == "failed":
                agent_stats[agent]["failed"] += 1
            if duration:
                agent_stats[agent]["durations"].append(duration)

        report = {}
        for agent, stats in agent_stats.items():
            durations = stats["durations"]
            report[agent] = {
                "total_tasks": stats["total"],
                "completed": stats["completed"],
                "failed": stats["failed"],
                "success_rate": round(stats["completed"] / stats["total"] * 100, 2) if stats["total"] else 0,
                "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else None,
                "min_duration_ms": min(durations) if durations else None,
                "max_duration_ms": max(durations) if durations else None,
            }
        return {"agent_performance": report}

    def trend_report(self, items: List[Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        time_window = metadata.get("time_window", "day")
        trends = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            created_at = item.get("created_at") or item.get("result", {}).get("created_at")
            if not created_at:
                continue
            try:
                dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                key = dt.strftime("%Y-%m-%d" if time_window == "day" else "%Y-%m-%d %H:00")
                trends[key] = trends.get(key, 0) + 1
            except Exception:
                pass
        return {"trends": trends, "time_window": time_window}

    def export_report(
        self,
        items: List[Any],
        format: str = "json",
        output_path: str = "report.json",
    ) -> Dict[str, Any]:
        report = self.detailed_report(items, {})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            return {"status": "success", "path": output_path, "format": "json"}

        if format == "csv":
            rows = report.get("items", [])
            if not rows:
                return {"status": "error", "message": "No data to export"}
            fieldnames = sorted({key for row in rows if isinstance(row, dict) for key in row.keys()})
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    if isinstance(row, dict):
                        writer.writerow(row)
            return {"status": "success", "path": output_path, "format": "csv", "rows": len(rows)}

        if format == "markdown":
            md = self._to_markdown(report)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
            return {"status": "success", "path": output_path, "format": "markdown"}

        return {"status": "error", "message": f"Unsupported format: {format}"}

    def _to_markdown(self, report: Dict[str, Any]) -> str:
        lines = [
            f"# Report Generated at {report.get('generated_at', 'unknown')}",
            "",
            f"## Summary",
            f"- Total Tasks: {report.get('total', 0)}",
            f"- Completed: {report.get('completed', 0)}",
            f"- Failed: {report.get('failed', 0)}",
            f"- Success Rate: {report.get('success_rate', 0)}%",
            "",
            "## Agents Used",
        ]
        for agent, count in report.get("agents_used", {}).items():
            lines.append(f"- {agent}: {count} tasks")
        lines.append("")
        lines.append("## Items")
        for item in report.get("items", []):
            if isinstance(item, dict):
                lines.append(f"- **{item.get('agent', 'unknown')}**: {item.get('description', 'N/A')} - {item.get('status', 'unknown')}")
        return "\n".join(lines)

    def _status(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("status", "unknown"))
        return str(getattr(item, "status", "unknown"))