"""
Export utility for automotive analysis reports.
Supports structured CSV, JSON, and Markdown formats with verified citations and timestamps.
"""
import csv
import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, List


class AnalysisExporter:
    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    @classmethod
    def export_components_csv(cls, data: Dict[str, Any]) -> str:
        """Export extracted software components and ports to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Export Timestamp",
            "Document Filename",
            "Component Name",
            "Component Type",
            "Cycle Time",
            "ASIL Level",
            "Port Count",
            "Ports List",
            "Status",
            "Citation",
        ])

        filename = data.get("filename", "Unknown")
        ts = cls._timestamp()
        components = data.get("components", [])

        for c in components:
            ports_str = "; ".join([
                f"{p['name']} ({p.get('port_type', '')} -> {p.get('interface', '')})"
                for p in c.get("ports", [])
            ])
            writer.writerow([
                ts,
                filename,
                c.get("name", ""),
                c.get("component_type", ""),
                c.get("cycle_time_ms", ""),
                c.get("asil_level", ""),
                len(c.get("ports", [])),
                ports_str,
                c.get("status", "Candidate - Requires Human Verification"),
                c.get("citation", ""),
            ])

        return output.getvalue()

    @classmethod
    def export_inconsistencies_csv(cls, data: Dict[str, Any]) -> str:
        """Export inconsistency findings to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Export Timestamp",
            "Document Filename",
            "Category",
            "Severity",
            "Title",
            "Affected SWC",
            "Details",
            "Verification Label",
            "Evidence Citation",
        ])

        filename = data.get("filename", "Unknown")
        ts = cls._timestamp()
        findings = data.get("findings", [])

        for f in findings:
            writer.writerow([
                ts,
                filename,
                f.get("category", ""),
                f.get("severity", ""),
                f.get("title", ""),
                f.get("affected_swc", ""),
                f.get("details", ""),
                f.get("verification_label", ""),
                f.get("evidence_citation", ""),
            ])

        return output.getvalue()

    @classmethod
    def export_comparison_markdown(cls, data: Dict[str, Any]) -> str:
        """Export document comparison results as Markdown."""
        doc_a = data.get("doc_a", {}).get("filename", "Doc A")
        doc_b = data.get("doc_b", {}).get("filename", "Doc B")
        summary = data.get("summary", {})

        lines = [
            f"# AUTOSAR HLD Architecture Comparison Report",
            f"*Generated on: {cls._timestamp()}*",
            "",
            f"- **Base Document (A):** `{doc_a}`",
            f"- **Target Document (B):** `{doc_b}`",
            "",
            "## 1. Executive Delta Summary",
            f"- Added Components: **{summary.get('added_count', 0)}**",
            f"- Removed Components: **{summary.get('removed_count', 0)}**",
            f"- Modified Components: **{summary.get('modified_count', 0)}**",
            f"- Unchanged Components: **{summary.get('unchanged_count', 0)}**",
            "",
            "## 2. Added Software Components",
        ]

        added = data.get("added_components", [])
        if added:
            for item in added:
                lines.append(f"### + `{item['component_name']}` ({item.get('type')})")
                lines.append(f"- **Cycle Time:** {item.get('cycle_time')} | **ASIL:** {item.get('asil')}")
                lines.append(f"- **Engineering Impact:** {item.get('engineering_impact')}")
                lines.append(f"- **Evidence:** {item.get('citation')}")
                lines.append("")
        else:
            lines.append("*No new components added.*")

        lines.extend(["", "## 3. Modified Components"])
        modified = data.get("modified_components", [])
        if modified:
            for item in modified:
                lines.append(f"### ~ `{item['component_name']}`")
                for chg in item.get("changes", []):
                    lines.append(f"- Change: {chg}")
                lines.append(f"- **Engineering Impact:** {item.get('engineering_impact')}")
                lines.append(f"- **Doc A Citation:** {item.get('doc_a_citation')}")
                lines.append(f"- **Doc B Citation:** {item.get('doc_b_citation')}")
                lines.append("")
        else:
            lines.append("*No modified components detected.*")

        lines.extend(["", "## 4. Verification Note", f"> {data.get('verification_note', '')}"])
        return "\n".join(lines)

    @classmethod
    def export_json(cls, data: Dict[str, Any]) -> str:
        """Export raw analysis result as formatted JSON with timestamp."""
        export_payload = {
            "exported_at": cls._timestamp(),
            "data": data,
        }
        return json.dumps(export_payload, indent=2)


analysis_exporter = AnalysisExporter()
