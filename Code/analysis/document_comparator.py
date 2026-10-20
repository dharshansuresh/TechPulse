"""
Document Comparison Engine for AUTOSAR HLD revisions.
Compares two documents (e.g. v1.0 vs v2.0), detects additions, removals, and modifications
in SWCs, ports, cycle times, and ASIL levels, citing exact pages for both documents.
Distinguishes raw textual differences from confirmed engineering impact.
"""
from typing import Dict, Any, List
from analysis.component_extractor import component_extractor
from rag.retriever import retriever
from core.logging_config import logger


class DocumentComparator:
    def compare_documents(
        self,
        doc_a_id: str,
        doc_a_name: str,
        doc_b_id: str,
        doc_b_name: str,
    ) -> Dict[str, Any]:
        """
        Perform bidirectional architectural comparison between Document A and Document B.
        """
        logger.info(f"Comparing Document A ({doc_a_name}) vs Document B ({doc_b_name})")

        # 1. Extract components for both documents
        res_a = component_extractor.extract_components(doc_a_id, doc_a_name)
        res_b = component_extractor.extract_components(doc_b_id, doc_b_name)

        comps_a = {c["name"]: c for c in res_a.get("components", [])}
        comps_b = {c["name"]: c for c in res_b.get("components", [])}

        names_a = set(comps_a.keys())
        names_b = set(comps_b.keys())

        added_names = names_b - names_a
        removed_names = names_a - names_b
        common_names = names_a & names_b

        added_components: List[Dict[str, Any]] = []
        for name in sorted(added_names):
            c = comps_b[name]
            added_components.append({
                "component_name": name,
                "type": c.get("component_type"),
                "cycle_time": c.get("cycle_time_ms"),
                "asil": c.get("asil_level"),
                "citation": c.get("citation"),
                "engineering_impact": (
                    f"New component introduced in {doc_b_name}. "
                    "Requires allocation to ECU task schedule and new RTE port mapping."
                ),
            })

        removed_components: List[Dict[str, Any]] = []
        for name in sorted(removed_names):
            c = comps_a[name]
            removed_components.append({
                "component_name": name,
                "type": c.get("component_type"),
                "citation": c.get("citation"),
                "engineering_impact": (
                    f"Component retired or refactored in {doc_b_name}. "
                    "Verify no remaining downstream consumers depend on its provided ports."
                ),
            })

        modified_components: List[Dict[str, Any]] = []
        for name in sorted(common_names):
            ca = comps_a[name]
            cb = comps_b[name]
            diffs = []
            eng_impacts = []

            # Compare cycle times
            if ca.get("cycle_time_ms") != cb.get("cycle_time_ms"):
                diffs.append(f"Cycle time changed: '{ca.get('cycle_time_ms')}' -> '{cb.get('cycle_time_ms')}'")
                eng_impacts.append("OS task period adjusted. May impact bus communication rate and CPU load.")

            # Compare ASIL levels
            if ca.get("asil_level") != cb.get("asil_level"):
                diffs.append(f"Safety level changed: '{ca.get('asil_level')}' -> '{cb.get('asil_level')}'")
                eng_impacts.append("Safety classification altered. Requires re-assessment of Safety Goals and FSRs.")

            # Compare ports count
            ports_a_names = {p["name"] for p in ca.get("ports", [])}
            ports_b_names = {p["name"] for p in cb.get("ports", [])}
            if ports_a_names != ports_b_names:
                new_ports = ports_b_names - ports_a_names
                dropped_ports = ports_a_names - ports_b_names
                if new_ports:
                    diffs.append(f"New ports added: {', '.join(new_ports)}")
                    eng_impacts.append("Additional RTE connector interfaces required.")
                if dropped_ports:
                    diffs.append(f"Ports removed: {', '.join(dropped_ports)}")
                    eng_impacts.append("Interface deprecation; potential break in existing RTE connections.")

            if diffs:
                modified_components.append({
                    "component_name": name,
                    "changes": diffs,
                    "engineering_impact": " ".join(eng_impacts),
                    "doc_a_citation": ca.get("citation"),
                    "doc_b_citation": cb.get("citation"),
                })

        # Summary of differences
        return {
            "doc_a": {"id": doc_a_id, "filename": doc_a_name},
            "doc_b": {"id": doc_b_id, "filename": doc_b_name},
            "summary": {
                "total_in_a": len(names_a),
                "total_in_b": len(names_b),
                "added_count": len(added_components),
                "removed_count": len(removed_components),
                "modified_count": len(modified_components),
                "unchanged_count": len(common_names) - len(modified_components),
            },
            "added_components": added_components,
            "removed_components": removed_components,
            "modified_components": modified_components,
            "verification_note": (
                "Textual differences are automatically categorized above. "
                "Architects must review identified changes against ARXML descriptors to confirm actual runtime delta."
            ),
        }


document_comparator = DocumentComparator()
