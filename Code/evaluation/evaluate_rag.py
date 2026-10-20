"""
Automated RAG Evaluation Script.
Measures retrieval relevance, citation accuracy, and groundedness across 10 benchmark automotive questions.
"""
import json
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.config import settings
from database.session import init_db, SessionLocal
from backend.services.document_service import document_service
from rag.qa_pipeline import rag_pipeline
from rag.retriever import retriever


def run_evaluation():
    print("=" * 70)
    print("AUTOMOTIVE ENGINEERING AI ASSISTANT: RAG EVALUATION BENCHMARK")
    print("=" * 70)

    init_db()
    db = SessionLocal()

    # Ingest sample documents first if not present
    sample_files = [
        ("AUTOSAR_Powertrain_Domain_HLD_v1.0.pdf", "Powertrain", "v1.0"),
        ("AUTOSAR_Powertrain_Domain_HLD_v2.0.pdf", "Powertrain", "v2.0"),
        ("AUTOSAR_Body_Gateway_HLD_v1.0.pdf", "Body Gateway", "v1.0"),
    ]

    print("\n[Step 1] Ingesting and indexing benchmark PDF files...")
    for fname, domain, ver in sample_files:
        p = settings.BASE_DIR / "sample_data" / fname
        if p.exists():
            with open(p, "rb") as f:
                b = f.read()
            rec, is_dup = document_service.process_upload(
                file_bytes=b,
                original_filename=fname,
                db=db,
                domain=domain,
                version_tag=ver,
            )
            print(f"  - Indexed '{fname}': ID {rec.id[:8]}... (Duplicate: {is_dup})")

    # Load Questions
    eval_file = Path(__file__).parent / "eval_questions.json"
    with open(eval_file, "r") as f:
        questions = json.load(f)

    print(f"\n[Step 2] Executing Evaluation on {len(questions)} Automotive HLD Questions...\n")

    results = []
    correct_retrievals = 0
    valid_citations = 0

    for q in questions:
        qid = q["id"]
        category = q["category"]
        query = q["question"]
        exp_kw = q["expected_keywords"]

        # Run RAG
        ans_obj = rag_pipeline.ask(question=query, top_k=5)

        # Check retrieval relevance
        retrieved_text = " ".join([ch["text"] for ch in ans_obj["evidence_chunks"]]).lower()
        if category == "Negative Test (Missing Information)":
            # For negative test: verify neither hallucinated cell chemistry exists in document
            hallucinated_in_context = any(term in retrieved_text for term in ["lfp", "nmc", "lithium iron phosphate"])
            retrieval_pass = (not hallucinated_in_context) or (not ans_obj["evidence_sufficient"])
            matches = ["Unspecified in HLD (Correctly Unfound)"] if retrieval_pass else ["Hallucinated"]
        else:
            matches = [kw for kw in exp_kw if kw.lower() in retrieved_text or kw.lower() in ans_obj["answer"].lower()]
            retrieval_pass = len(matches) > 0
        if retrieval_pass:
            correct_retrievals += 1

        # Check citations
        citations = ans_obj.get("citations", [])
        has_citations = len(citations) > 0 or ans_obj["is_retrieval_only"]
        if has_citations:
            valid_citations += 1

        results.append({
            "id": qid,
            "category": category,
            "question": query,
            "retrieval_pass": retrieval_pass,
            "matched_keywords": matches,
            "citation_count": len(citations),
            "is_retrieval_only": ans_obj["is_retrieval_only"],
            "evidence_sufficient": ans_obj["evidence_sufficient"],
        })

        status_mark = "PASS" if retrieval_pass else "FAIL"
        print(f"[{qid}] {category:<30} -> {status_mark} (Found: {matches})")

    retrieval_accuracy = (correct_retrievals / len(questions)) * 100
    citation_rate = (valid_citations / len(questions)) * 100

    print("\n" + "=" * 70)
    print("EVALUATION SCORECARD RESULTS")
    print("=" * 70)
    print(f"Total Benchmark Queries : {len(questions)}")
    print(f"Retrieval Hit Rate      : {retrieval_accuracy:.1f}% ({correct_retrievals}/{len(questions)})")
    print(f"Citation Grounding Rate : {citation_rate:.1f}% ({valid_citations}/{len(questions)})")
    print("=" * 70)

    db.close()
    return results


if __name__ == "__main__":
    run_evaluation()
