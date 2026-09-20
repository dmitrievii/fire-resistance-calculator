"""Stable public facade for the REPORT-IR Markdown renderer."""
from .report_markdown_impl import REPORT_MARKDOWN_CONTRACT, render_report_markdown

__all__ = ["REPORT_MARKDOWN_CONTRACT", "render_report_markdown"]
