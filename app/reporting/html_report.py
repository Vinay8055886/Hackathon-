"""HTML report generation (Jinja2)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Finding, Run, Target

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def build_html_report(run: Run, target: Target, findings: list[Finding]) -> str:
    template = _ENV.get_template("report.jinja2")
    return template.render(run=run, target=target, findings=findings)
