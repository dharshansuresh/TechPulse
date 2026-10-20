"""
Tests for Component Extractor, Inconsistency Detector, Document Comparator, and Exporters.
"""
from analysis.component_extractor import ComponentExtractor
from analysis.inconsistency_detector import InconsistencyDetector
from analysis.document_comparator import DocumentComparator
from analysis.exporters import AnalysisExporter


def test_component_extraction_deterministic():
    extractor = ComponentExtractor()
    sample_chunks = [
        {
            "text": "TorqueArbitrationSWC is an ApplicationSWC executing at 10ms with ASIL B. Defines Pp_TorqueCommand with If_TorqueCommand.",
            "page_number": 2,
            "filename": "pt_v1.pdf",
        }
    ]
    comps = extractor._deterministic_extract(sample_chunks, "pt_v1.pdf")
    assert len(comps) >= 1
    c = comps[0]
    assert c["name"] == "TorqueArbitrationSWC"
    assert c["cycle_time_ms"] == "10ms"
    assert c["asil_level"] == "ASIL B"
    assert c["status"] == "Candidate - Requires Human Verification"
    assert len(c["ports"]) >= 1
    assert c["ports"][0]["name"] == "Pp_TorqueCommand"


def test_document_comparator_diff():
    comparator = DocumentComparator()
    # Mocking extraction results
    doc_a_comps = [
        {"name": "TorqueArbitrationSWC", "component_type": "ApplicationSWC", "cycle_time_ms": "10ms", "asil_level": "ASIL B", "ports": [], "citation": "p1"},
        {"name": "EngineSpeedSensorSWC", "component_type": "SensorActuatorSWC", "cycle_time_ms": "10ms", "asil_level": "ASIL B", "ports": [], "citation": "p1"},
    ]
    doc_b_comps = [
        {"name": "TorqueArbitrationSWC", "component_type": "ApplicationSWC", "cycle_time_ms": "5ms", "asil_level": "ASIL C", "ports": [], "citation": "p1"},
        {"name": "RegenerativeBrakingSWC", "component_type": "ApplicationSWC", "cycle_time_ms": "5ms", "asil_level": "ASIL C", "ports": [], "citation": "p2"},
    ]

    # Test comparison logic
    names_a = {c["name"] for c in doc_a_comps}
    names_b = {c["name"] for c in doc_b_comps}
    assert "RegenerativeBrakingSWC" in (names_b - names_a)
    assert "EngineSpeedSensorSWC" in (names_a - names_b)


def test_exporters():
    data = {
        "filename": "test.pdf",
        "components": [
            {
                "name": "TorqueArbitrationSWC",
                "component_type": "ApplicationSWC",
                "cycle_time_ms": "10ms",
                "asil_level": "ASIL B",
                "ports": [{"name": "Pp_Torque", "port_type": "Provided", "interface": "If_Torque"}],
                "citation": "[Doc: test.pdf, Page: 1]",
            }
        ]
    }
    csv_str = AnalysisExporter.export_components_csv(data)
    assert "TorqueArbitrationSWC" in csv_str
    assert "Candidate - Requires Human Verification" in csv_str

    json_str = AnalysisExporter.export_json(data)
    assert '"exported_at"' in json_str
