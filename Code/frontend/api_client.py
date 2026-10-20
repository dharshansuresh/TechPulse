"""
API Client for Streamlit Frontend.
Communicates with FastAPI REST backend, with seamless fallback to direct
service invocation if the REST server is not started yet.
"""
from typing import Dict, Any, List, Optional
import requests
from core.config import settings
from core.logging_config import logger
from database.session import SessionLocal
from database.repository import DocumentRepository
from backend.services.document_service import document_service
from rag.qa_pipeline import rag_pipeline
from rag.retriever import retriever
from analysis.summarizer import summarizer
from analysis.component_extractor import component_extractor
from analysis.inconsistency_detector import inconsistency_detector
from analysis.document_comparator import document_comparator


class APIClient:
    def __init__(self, base_url: str = settings.BACKEND_API_URL):
        self.base_url = base_url.rstrip("/")

    def is_backend_live(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    # 1. Documents
    def list_documents(self) -> List[Dict[str, Any]]:
        if self.is_backend_live():
            try:
                r = requests.get(f"{self.base_url}/documents", timeout=5)
                if r.status_code == 200:
                    return r.json().get("documents", [])
            except Exception:
                pass
        # Fallback to direct DB query
        db = SessionLocal()
        try:
            docs = DocumentRepository.list_documents(db)
            return [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "page_count": d.page_count,
                    "file_size_bytes": d.file_size_bytes,
                    "status": d.status,
                    "ocr_warning": d.ocr_warning,
                    "version_tag": d.version_tag,
                    "domain": d.domain,
                    "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else "",
                    "error_message": d.error_message,
                }
                for d in docs
            ]
        finally:
            db.close()

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        domain: str = "Powertrain",
        version_tag: str = "v1.0",
    ) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                files = {"file": (filename, file_bytes, "application/pdf")}
                data = {"domain": domain, "version_tag": version_tag}
                r = requests.post(f"{self.base_url}/documents/upload", files=files, data=data, timeout=30)
                if r.status_code in [200, 201]:
                    return r.json()
                else:
                    return {"error": r.json().get("detail", "Upload failed")}
            except Exception as e:
                logger.warning(f"REST upload failed: {e}. Using direct service.")

        db = SessionLocal()
        try:
            rec, is_dup = document_service.process_upload(
                file_bytes=file_bytes,
                original_filename=filename,
                db=db,
                domain=domain,
                version_tag=version_tag,
            )
            return {
                "message": "Indexed successfully" if not is_dup else "Duplicate file identified",
                "is_duplicate": is_dup,
                "document": {
                    "id": rec.id,
                    "filename": rec.filename,
                    "page_count": rec.page_count,
                    "status": rec.status,
                    "ocr_warning": rec.ocr_warning,
                },
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def delete_document(self, document_id: str) -> bool:
        if self.is_backend_live():
            try:
                r = requests.delete(f"{self.base_url}/documents/{document_id}", timeout=10)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
        db = SessionLocal()
        try:
            return document_service.delete_document(document_id, db)
        finally:
            db.close()

    def reindex_document(self, document_id: str) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                r = requests.post(f"{self.base_url}/documents/{document_id}/index", timeout=30)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        db = SessionLocal()
        try:
            count = document_service.index_document(document_id, db)
            return {"document_id": document_id, "chunks_indexed": count, "status": "indexed"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    # 2. Chat & QA
    def ask_chat(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                payload = {"question": question, "document_id": document_id, "top_k": top_k}
                r = requests.post(f"{self.base_url}/chat/ask", json=payload, timeout=60)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                logger.warning(f"REST chat request failed: {e}. Using direct service.")
        return rag_pipeline.ask(question=question, document_id=document_id, top_k=top_k)

    # 3. Search
    def search_term(self, query: str, document_id: Optional[str] = None, top_k: int = 6) -> List[Dict[str, Any]]:
        if self.is_backend_live():
            try:
                r = requests.post(
                    f"{self.base_url}/search",
                    json={"query": query, "document_id": document_id, "top_k": top_k},
                    timeout=15,
                )
                if r.status_code == 200:
                    return r.json().get("results", [])
            except Exception:
                pass
        return retriever.retrieve(query=query, document_id=document_id, top_k=top_k)

    # 4. Analysis
    def get_summary(self, document_id: str, filename: str, page_count: int) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                r = requests.post(f"{self.base_url}/analysis/summary", json={"document_id": document_id}, timeout=45)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return summarizer.summarize_document(document_id, filename, page_count)

    def extract_components(self, document_id: str, filename: str) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                r = requests.post(f"{self.base_url}/analysis/components", json={"document_id": document_id}, timeout=45)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return component_extractor.extract_components(document_id, filename)

    def detect_inconsistencies(self, document_id: str, filename: str, sec_doc_id: str = None) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                r = requests.post(
                    f"{self.base_url}/analysis/inconsistencies",
                    json={"document_id": document_id, "secondary_document_id": sec_doc_id},
                    timeout=45,
                )
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return inconsistency_detector.detect_inconsistencies(document_id, filename, sec_doc_id)

    def compare_documents(self, doc_a_id: str, doc_a_name: str, doc_b_id: str, doc_b_name: str) -> Dict[str, Any]:
        if self.is_backend_live():
            try:
                r = requests.post(
                    f"{self.base_url}/analysis/compare",
                    json={"doc_a_id": doc_a_id, "doc_b_id": doc_b_id},
                    timeout=45,
                )
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return document_comparator.compare_documents(doc_a_id, doc_a_name, doc_b_id, doc_b_name)


api_client = APIClient()
