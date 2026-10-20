"""
Text chunking module with automotive technical terminology preservation.
Maintains exact original page numbers for RAG citation integrity.
"""
import re
from typing import List, Dict, Any
from core.config import settings
from core.logging_config import logger


class DocumentChunker:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_extracted_pages(
        self,
        document_id: str,
        filename: str,
        pages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Takes page-by-page extracted data and produces overlapping chunks.
        Guarantees that every chunk has a well-defined original page number.
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data.get("text", "").strip()

            if not page_text:
                continue

            page_chunks = self._chunk_text(page_text)
            for local_idx, ch_text in enumerate(page_chunks):
                chunk_id = f"{document_id}_p{page_num}_c{local_idx + 1}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_num,
                    "chunk_index": global_chunk_idx,
                    "text": ch_text,
                    "char_count": len(ch_text),
                    "token_count": max(1, len(ch_text) // 4),
                })
                global_chunk_idx += 1

        logger.info(f"Chunked {filename}: {len(pages)} pages -> {len(chunks)} chunks.")
        return chunks

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks respecting paragraphs and sentences,
        avoiding breaking technical identifiers like Rte_Write_*, 0x10, etc.
        """
        if len(text) <= self.chunk_size:
            return [text]

        # First split into natural paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            # If paragraph itself is larger than chunk_size, split by sentences or line breaks
            if len(para) > self.chunk_size:
                sub_parts = self._split_large_paragraph(para)
                for part in sub_parts:
                    if len(current_chunk) + len(part) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk}\n{part}" if current_chunk else part
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = part
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    # Overlap handling: take tail of previous chunk if overlap configured
                    if self.chunk_overlap > 0 and chunks:
                        overlap_text = chunks[-1][-self.chunk_overlap:]
                        current_chunk = f"...{overlap_text}\n\n{para}"
                    else:
                        current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph into sentences or fixed window slices."""
        # Use sentence boundary that doesn't split on dots inside abbreviations (e.g., v1.0, 0.5, etc.)
        sentence_splits = re.split(r"(?<=[a-zA-Z0-9\)])\.\s+(?=[A-Z])", paragraph)
        sub_chunks: List[str] = []
        cur = ""
        for s in sentence_splits:
            if len(cur) + len(s) + 2 <= self.chunk_size:
                cur = f"{cur}. {s}" if cur else s
            else:
                if cur:
                    sub_chunks.append(cur)
                # If a single sentence exceeds chunk size, split by character window
                if len(s) > self.chunk_size:
                    step = max(100, self.chunk_size - self.chunk_overlap)
                    for i in range(0, len(s), step):
                        sub_chunks.append(s[i : i + self.chunk_size])
                    cur = ""
                else:
                    cur = s
        if cur:
            sub_chunks.append(cur)
        return sub_chunks
