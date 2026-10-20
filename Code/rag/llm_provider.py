"""
LLM Provider abstraction supporting OpenAI, Gemini, Ollama, and a zero-dependency
Retrieval-Only synthesis engine when no LLM API key is configured.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
import requests
from core.config import settings
from core.logging_config import logger


@dataclass
class LLMResult:
    text: str
    provider: str
    is_retrieval_only: bool
    model: str
    tokens_used: int = 0
    privacy_notice: Optional[str] = None


class LLMProvider:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.openai_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY).strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY).strip()
        self.ollama_url = settings.OLLAMA_BASE_URL.strip()

    def get_active_provider_info(self) -> Dict[str, Any]:
        """Detect available LLM capability."""
        if self.gemini_key and (self.provider in ["auto", "gemini"]):
            return {
                "provider": "gemini",
                "model": settings.GEMINI_MODEL,
                "type": "Cloud API (External)",
                "ready": True,
                "privacy_alert": "Document context is transmitted externally to Google Gemini API.",
            }
        if self.openai_key and (self.provider in ["auto", "openai"]):
            return {
                "provider": "openai",
                "model": settings.OPENAI_MODEL,
                "type": "Cloud API (External)",
                "ready": True,
                "privacy_alert": "Document context is transmitted externally to OpenAI-compatible endpoint.",
            }
        if self.provider == "ollama":
            return {
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
                "type": "Local Host (On-Premises)",
                "ready": True,
                "privacy_alert": "Local on-premises inference via Ollama.",
            }
        return {
            "provider": "retrieval_only",
            "model": "Semantic Extraction Engine (No API Key Required)",
            "type": "Local Offline Retrieval",
            "ready": True,
            "privacy_alert": "No external LLM calls. Data remains 100% local on this machine.",
        }

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context_chunks: List[Dict[str, Any]],
    ) -> LLMResult:
        """
        Generate answer from prompt and context.
        Falls back smoothly to Retrieval-Only synthesis if LLM is unavailable or unconfigured.
        """
        info = self.get_active_provider_info()
        active_prov = info["provider"]

        if active_prov == "gemini":
            try:
                return self._call_gemini(prompt, system_prompt, info["model"])
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}). Falling back to Retrieval-Only mode.")

        elif active_prov == "openai":
            try:
                return self._call_openai(prompt, system_prompt, info["model"])
            except Exception as e:
                logger.warning(f"OpenAI API call failed ({e}). Falling back to Retrieval-Only mode.")

        elif active_prov == "ollama":
            try:
                return self._call_ollama(prompt, system_prompt, info["model"])
            except Exception as e:
                logger.warning(f"Ollama local call failed ({e}). Falling back to Retrieval-Only mode.")

        # Default: Retrieval-Only synthesis mode
        return self._synthesize_retrieval_only(prompt, context_chunks)

    def _call_gemini(self, prompt: str, system_prompt: str, model_name: str) -> LLMResult:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )
        response = model.generate_content(prompt)
        text = response.text if response and hasattr(response, "text") else "No response generated."
        return LLMResult(
            text=text,
            provider="Google Gemini",
            is_retrieval_only=False,
            model=model_name,
            privacy_notice="Notice: Prompt and context excerpts were sent to Google Gemini cloud API.",
        )

    def _call_openai(self, prompt: str, system_prompt: str, model_name: str) -> LLMResult:
        base_url = settings.OPENAI_BASE_URL.rstrip("/") if settings.OPENAI_BASE_URL else "https://api.openai.com/v1"
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return LLMResult(
            text=text,
            provider="OpenAI / Compatible API",
            is_retrieval_only=False,
            model=model_name,
            tokens_used=tokens,
            privacy_notice="Notice: Prompt and context excerpts were sent to OpenAI-compatible endpoint.",
        )

    def _call_ollama(self, prompt: str, system_prompt: str, model_name: str) -> LLMResult:
        endpoint = f"{self.ollama_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        resp = requests.post(endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data["message"]["content"]
        return LLMResult(
            text=text,
            provider="Ollama (Local)",
            is_retrieval_only=False,
            model=model_name,
            privacy_notice="Notice: Inference processed locally on-premises via Ollama.",
        )

    def _synthesize_retrieval_only(
        self,
        prompt: str,
        context_chunks: List[Dict[str, Any]],
    ) -> LLMResult:
        """
        Grounded offline synthesis when no external LLM is configured.
        Presents structured citations and extracted engineering passages.
        """
        if not context_chunks:
            msg = (
                "### Evidence-Grounded Response (Retrieval-Only Mode)\n\n"
                "**Result:** No relevant document evidence was found for your query in the indexed HLD repository.\n\n"
                "*Tip:* Please verify that target automotive PDF documents have been uploaded and indexed, "
                "or try searching for specific AUTOSAR keywords (e.g., `Rte_`, `SWC`, `CAN`, `ASIL`, `DID`)."
            )
            return LLMResult(
                text=msg,
                provider="Offline Retrieval Engine",
                is_retrieval_only=True,
                model="Deterministic Extractor",
            )

        citations_list = []
        for ch in context_chunks:
            c = f"[Doc: {ch['filename']}, Page: {ch['page_number']}]"
            if c not in citations_list:
                citations_list.append(c)

        synthesis_lines = [
            "### Evidence-Grounded Response (Retrieval-Only Mode)",
            "",
            "> **Notice:** Running in **Retrieval-Only Mode** (Zero API keys required). "
            "Answers are synthesized directly from retrieved vector chunks to guarantee strict grounding without hallucination.",
            "",
            f"**Citations:** {', '.join(citations_list)}",
            "",
            "#### Relevant Architectural Evidence Found:",
        ]

        for i, ch in enumerate(context_chunks, 1):
            score_pct = int(ch.get("score", 0.0) * 100)
            synthesis_lines.append(
                f"**Evidence #{i}** — `{ch['filename']}` *(Page {ch['page_number']}, Relevance: {score_pct}%)*:"
            )
            # Indent text or quote
            quote_lines = ch["text"].strip().split("\n")
            formatted_quote = "\n".join(f"> {line}" for line in quote_lines if line.strip())
            synthesis_lines.append(formatted_quote)
            synthesis_lines.append("")

        synthesis_lines.append(
            "*(To enable generative prose answers, configure `GEMINI_API_KEY` or `OPENAI_API_KEY` in your `.env` file.)*"
        )

        return LLMResult(
            text="\n".join(synthesis_lines),
            provider="Offline Semantic Extractor",
            is_retrieval_only=True,
            model="Local Deterministic Vector Retrieval",
        )


llm_provider = LLMProvider()
