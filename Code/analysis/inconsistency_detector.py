"""
Architectural Inconsistency and Contradiction Detector.
Analyzes component interactions, port bindings, cycle times, and safety levels.
Includes strict non-compliance disclaimers and human verification tags.
"""
from typing import Dict, Any, List
from analysis.component_extractor import component_extractor
from rag.retriever import retriever
from core.logging_config import logger


class InconsistencyDetector:
    def detect_inconsistencies(
        self,
        document_id: str,
        filename: str,
        secondary_document_id: str = None,
        secondary_filename: str = None,
    ) -> Dict[str, Any]:
        """
        Analyze documents for interface mismatches, unmapped ports, timing discrepancies,
        and ASIL integrity concerns.
        """
        inconsistencies: List[Dict[str, Any]] = []

        # 1. Extract components for primary document
        primary_res = component_extractor.extract_components(document_id, filename)
        all_components = list(primary_res.get("components", []))

        # If secondary document is provided (e.g. comparing versions or multi-ECU setup)
        if secondary_document_id and secondary_filename:
            secondary_res = component_extractor.extract_components(secondary_document_id, secondary_filename)
            all_components.extend(secondary_res.get("components", []))

        # Check for unmapped required ports
        provided_ports = set()
        required_ports = []

        for c in all_components:
            for p in c.get("ports", []):
                p_name = p.get("name", "")
                p_type = p.get("port_type", "")
                interface_name = p.get("interface", "")
                if "Provided" in p_type:
                    clean_name = p_name.replace("Pp_", "").replace("PPort_", "")
                    provided_ports.add(clean_name.lower())
                    if interface_name:
                        provided_ports.add(interface_name.lower())
                elif "Required" in p_type:
                    clean_name = p_name.replace("Rp_", "").replace("RPort_", "")
                    required_ports.append({
                        "swc": c.get("name"),
                        "port_name": p_name,
                        "clean_name": clean_name,
                        "interface": interface_name,
                        "citation": p.get("citation", c.get("citation")),
                    })

        # Flag unmapped ports
        for req in required_ports:
            key_name = req["clean_name"].lower()
            if_key = req["interface"].lower() if req["interface"] else ""
            has_provider = (key_name in provided_ports) or (if_key in provided_ports)
            if not has_provider and len(provided_ports) > 0:
                inconsistencies.append({
                    "category": "Unresolved Port Dependency",
                    "severity": "Medium",
                    "title": f"Required port `{req['port_name']}` has no corresponding Provided Port in scope",
                    "affected_swc": req["swc"],
                    "details": (
                        f"Software component `{req['swc']}` defines a Required Port `{req['port_name']}` "
                        f"(Interface: `{req['interface']}`), but no SWC in the analyzed document(s) exposes a matching P-Port."
                    ),
                    "evidence_citation": req["citation"],
                    "verification_label": "Potential Inconsistency - Requires Architectural Review",
                })

        # Check for cycle time conflicts
        cycle_times = {c.get("name"): c.get("cycle_time_ms") for c in all_components if c.get("cycle_time_ms") != "Not Specified"}
        if len(cycle_times) >= 2:
            fast_comps = [k for k, v in cycle_times.items() if "5ms" in v or "10ms" in v]
            slow_comps = [k for k, v in cycle_times.items() if "100ms" in v or "50ms" in v]
            if fast_comps and slow_comps:
                inconsistencies.append({
                    "category": "Timing & Sampling Rate Discrepancy",
                    "severity": "Low",
                    "title": "Disparate task execution periods across interconnected components",
                    "affected_swc": f"{fast_comps[0]} vs {slow_comps[0]}",
                    "details": (
                        f"Component `{fast_comps[0]}` executes at periodic rate `{cycle_times[fast_comps[0]]}` "
                        f"while `{slow_comps[0]}` runs at `{cycle_times[slow_comps[0]]}`. "
                        "Ensure the RTE buffer is configured with appropriate queueing or filter locks to prevent data starvation/jitter."
                    ),
                    "evidence_citation": f"[Doc: {filename}, Page: 1]",
                    "verification_label": "Design Advisory - Requires Timing Verification",
                })

        # Check for safety level (ASIL) interactions
        asil_ratings = {c.get("name"): c.get("asil_level") for c in all_components if c.get("asil_level") not in ["Unspecified", None]}
        high_safety = [k for k, v in asil_ratings.items() if "ASIL C" in v or "ASIL D" in v or "ASIL B" in v]
        qm_safety = [k for k, v in asil_ratings.items() if "QM" in v]
        if high_safety and qm_safety:
            inconsistencies.append({
                "category": "Functional Safety (ISO 26262) Boundary Notice",
                "severity": "Medium",
                "title": f"Safety boundary between {high_safety[0]} ({asil_ratings[high_safety[0]]}) and QM components",
                "affected_swc": f"{high_safety[0]} <-> {qm_safety[0]}",
                "details": (
                    f"Higher ASIL component `{high_safety[0]}` interacts with QM component `{qm_safety[0]}`. "
                    "Ensure Freedom from Interference (FFI), memory partitioning, and E2E signal protection are implemented."
                ),
                "evidence_citation": f"[Doc: {filename}, Page: 1]",
                "verification_label": "Safety Review Item - Requires Functional Safety Manager Sign-Off",
            })

        disclaimer = (
            "NOTICE: These findings represent automated heuristic extractions from the provided text. "
            "They do NOT constitute a formal declaration of AUTOSAR standard non-compliance or ISO 26262 certification failure. "
            "Formal compliance requires verified ARXML models and authorized engineering tool qualification."
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "findings_count": len(inconsistencies),
            "findings": inconsistencies,
            "compliance_disclaimer": disclaimer,
        }


inconsistency_detector = InconsistencyDetector()
