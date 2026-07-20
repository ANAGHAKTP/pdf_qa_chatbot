import json
import csv
import io
from typing import Dict, Any

class EvaluationExporter:
    """
    Exports evaluation run results into JSON, CSV, Markdown, or HTML formats.
    """

    @classmethod
    def to_json(cls, report_data: Dict[str, Any]) -> str:
        return json.dumps(report_data, indent=2)

    @classmethod
    def to_csv(cls, report_data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])

        metrics = report_data.get("metrics", {})
        for k, v in metrics.items():
            writer.writerow([k, v])

        return output.getvalue()

    @classmethod
    def to_markdown(cls, report_data: Dict[str, Any]) -> str:
        run_id = report_data.get("run_id", "EVAL-000")
        dataset = report_data.get("dataset", "Unknown")
        model = report_data.get("model", "Gemini-1.5")
        metrics = report_data.get("metrics", {})

        md = f"# Evaluation Report: {run_id}\n\n"
        md += f"**Dataset**: {dataset}\n"
        md += f"**Model**: {model}\n\n"
        md += "## Key Metrics\n\n"
        md += "| Metric | Value |\n|---|---|\n"

        for k, v in metrics.items():
            md += f"| {k} | {v} |\n"

        return md

    @classmethod
    def to_html(cls, report_data: Dict[str, Any]) -> str:
        run_id = report_data.get("run_id", "EVAL-000")
        dataset = report_data.get("dataset", "Unknown")
        metrics = report_data.get("metrics", {})

        rows = "".join(f"<tr><td style='padding:8px;border:1px solid #333;'>{k}</td><td style='padding:8px;border:1px solid #333;'>{v}</td></tr>" for k, v in metrics.items())

        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Evaluation Report - {run_id}</title></head>
        <body style="font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:20px;">
          <h2>DOCMind Evaluation Report: {run_id}</h2>
          <p><strong>Dataset:</strong> {dataset}</p>
          <table style="border-collapse:collapse;width:100%;max-width:600px;">
            <thead><tr style="background:#161b22;"><th style="padding:8px;border:1px solid #333;">Metric</th><th style="padding:8px;border:1px solid #333;">Value</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </body>
        </html>
        """
