from typing import Any, Dict, List, Optional
from src.agents.base.base_agent import BaseAgent
from src.core.task import Task


class EmailAgent(BaseAgent):
    """Email worker agent with templates, attachments, and scheduling."""

    TEMPLATES = {
        "proposal": {
            "subject": "Business Proposal: {company_name}",
            "body": """Dear {contact_name},

Thank you for your interest in our services. We are pleased to present a proposal tailored to {company_name}'s needs.

{proposal_details}

We would love to discuss this further at your convenience.

Best regards,
{sender_name}
{sender_title}
{sender_company}""",
        },
        "follow_up": {
            "subject": "Following up: {previous_topic}",
            "body": """Hi {contact_name},

I wanted to follow up on our previous conversation about {previous_topic}.

{follow_up_details}

Please let me know if you have any questions.

Best regards,
{sender_name}""",
        },
        "meeting_request": {
            "subject": "Meeting Request: {meeting_topic}",
            "body": """Dear {contact_name},

I would like to schedule a meeting to discuss {meeting_topic}.

Proposed times:
{proposed_times}

Please let me know what works best for you.

Best regards,
{sender_name}""",
        },
        "invoice": {
            "subject": "Invoice #{invoice_number} - {company_name}",
            "body": """Dear {contact_name},

Please find attached invoice #{invoice_number} for {amount_due}.

Due date: {due_date}

{line_items}

Thank you for your business.

Best regards,
{sender_name}
{sender_company}""",
        },
        "welcome": {
            "subject": "Welcome to {company_name}!",
            "body": """Hi {contact_name},

Welcome to {company_name}! We're excited to have you on board.

{welcome_details}

If you have any questions, feel free to reach out.

Best regards,
{sender_name}""",
        },
    }

    def __init__(self, email_tool=None, llm=None):
        super().__init__(
            name="Email Agent",
            description="Drafts and sends business emails with templates and scheduling",
            tools=[email_tool] if email_tool else [],
            llm=llm,
        )
        self.email_tool = email_tool

    def list_templates(self) -> Dict[str, Dict[str, str]]:
        return {name: {"subject": t["subject"], "body_preview": t["body"][:100] + "..."} for name, t in self.TEMPLATES.items()}

    def render_template(self, template_name: str, variables: Dict[str, str]) -> Dict[str, str]:
        template = self.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        # Use safe formatting with defaults for missing keys
        safe_vars = {**{"sender_title": "", "sender_company": "", "proposal_details": "", 
                       "follow_up_details": "", "proposed_times": "", "invoice_number": "",
                       "amount_due": "", "due_date": "", "line_items": "", "welcome_details": "",
                       "previous_topic": "", "meeting_topic": ""}, **variables}
        subject = template["subject"].format(**safe_vars)
        body = template["body"].format(**safe_vars)
        return {"subject": subject, "body": body}

    def generate_email_with_llm(self, task: Task) -> Dict[str, str]:
        if not self.llm:
            raise ValueError("LLM not configured")
        prompt = f"""
You are a professional business email writer.
Write a concise, professional email based on the user's request.
Return JSON with keys: subject, body, to (if mentioned).

User request: {task.description}
Context: {task.metadata}
"""
        result = self.llm.generate_json(prompt, task_type="reasoning", default={})
        if isinstance(result, dict) and result.get("subject") and result.get("body"):
            return {"subject": result["subject"], "body": result["body"], "to": result.get("to", "")}
        return {"subject": "Business Email", "body": task.description, "to": ""}

    def run(self, task: Task):
        task.set_status("running")
        try:
            if not self.email_tool:
                raise RuntimeError("Email tool is not configured")

            template_name = task.metadata.get("template")
            variables = task.metadata.get("variables", {})
            # Also support flat metadata with dot notation (e.g., variables.contact_name)
            if not variables:
                variables = {k.replace("variables.", ""): v for k, v in task.metadata.items() if k.startswith("variables.")}
            use_llm = task.metadata.get("use_llm", False)

            if template_name:
                rendered = self.render_template(template_name, variables)
                subject = rendered["subject"]
                body = rendered["body"]
                to_email = variables.get("to_email", task.metadata.get("to", ""))
            elif use_llm and self.llm:
                generated = self.generate_email_with_llm(task)
                subject = generated["subject"]
                body = generated["body"]
                to_email = generated.get("to", task.metadata.get("to", ""))
            else:
                to_email = task.metadata.get("to", "")
                subject = task.metadata.get("subject", "Business update")
                body = task.metadata.get("body") or task.description

            dry_run = bool(task.metadata.get("dry_run", True))
            cc = task.metadata.get("cc", "")
            bcc = task.metadata.get("bcc", "")
            attachments = task.metadata.get("attachments", [])

            if not to_email:
                result = self.email_tool.draft(to_email, subject, body)
                result["message"] = "No recipient provided; draft only."
            else:
                result = self.email_tool.send(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    dry_run=dry_run,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                )

            task.set_result({"agent": self.name, "result": result})
        except Exception as exc:
            task.set_error(str(exc))
        return task.result