"""
Tests for vector store indexing, querying, and deletion in ChromaDB.
"""
import shutil
import tempfile
from pathlib import Path
from rag.vector_store import ChromaVectorStore


def test_vector_store_lifecycle():
    temp_dir = tempfile.mkdtemp()
    try:
        vs = ChromaVectorStore(persist_dir=temp_dir, collection_name="test_collection")

        sample_chunks = [
            {
                "chunk_id": "doc1_p1_c1",
                "document_id": "doc1",
                "filename": "powertrain_v1.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "text": "TorqueArbitrationSWC executes at 10ms cycle time under ASIL B.",
            },
            {
                "chunk_id": "doc1_p2_c1",
                "document_id": "doc1",
                "filename": "powertrain_v1.pdf",
                "page_number": 2,
                "chunk_index": 1,
                "text": "Diagnostic Event Manager records DTC 0x921401 for throttle mismatch.",
            },
            {
                "chunk_id": "doc2_p1_c1",
                "document_id": "doc2",
                "filename": "body_bcm.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "text": "DoorControlSWC manages central locking motors at 20ms.",
            },
        ]

        # 1. Indexing
        indexed_count = vs.index_chunks(sample_chunks)
        assert indexed_count == 3
        assert vs.count() == 3

        # 2. Querying without filter
        results = vs.query("What is the execution period of torque arbitration?", top_k=2)
        assert len(results) > 0
        assert "TorqueArbitrationSWC" in results[0]["text"]
        assert results[0]["filename"] == "powertrain_v1.pdf"

        # 3. Querying with document filter
        bcm_results = vs.query("central locking", document_id="doc2")
        assert len(bcm_results) > 0
        assert bcm_results[0]["document_id"] == "doc2"

        # 4. Deletion by document_id
        vs.delete_by_document_id("doc1")
        assert vs.count() == 1

        # doc1 results should no longer appear
        res_after = vs.query("torque arbitration", document_id="doc1")
        assert len(res_after) == 0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
