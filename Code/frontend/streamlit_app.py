"""
Streamlit Web User Interface for Automotive Engineering AI Assistant.
AUTOSAR High-Level Design (HLD) Document Analysis & Intelligence Platform.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from frontend.api_client import api_client
from rag.llm_provider import llm_provider
from analysis.exporters import analysis_exporter
from core.config import settings

# Page setup
st.set_page_config(
    page_title="Automotive AI Assistant - AUTOSAR HLD",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-live { background-color: #DEF7EC; color: #03543F; }
    .badge-local { background-color: #E1EFFE; color: #1E429F; }
    .badge-warn { background-color: #FDF6B2; color: #723B13; }
    .evidence-box {
        border-left: 4px solid #3B82F6;
        background-color: #F8FAFC;
        padding: 12px;
        margin-bottom: 12px;
        border-radius: 4px;
    }
    .citation-pill {
        display: inline-block;
        background: #EEF2FF;
        color: #3730A3;
        border: 1px solid #C7D2FE;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def load_sample_file(sample_path: Path):
    with open(sample_path, "rb") as f:
        bytes_data = f.read()
    return bytes_data, sample_path.name


# Navigation Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/car.png", width=64)
    st.markdown("### **Automotive AI Platform**")
    st.markdown("*AUTOSAR HLD Intelligence*")
    st.divider()

    # System Status Indicator
    backend_live = api_client.is_backend_live()
    prov_info = llm_provider.get_active_provider_info()

    if backend_live:
        st.markdown('<span class="status-badge badge-live">● FastAPI REST Live</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-local">● Local Embedded Engine</span>', unsafe_allow_html=True)

    st.caption(f"**LLM:** {prov_info['provider'].upper()} ({prov_info['type']})")
    if prov_info.get("privacy_alert"):
        st.info(prov_info["privacy_alert"], icon="🔒")

    st.divider()

    nav_choice = st.radio(
        "Navigation",
        [
            "📂 1. Document Library & Upload",
            "💬 2. Grounded Q&A Assistant",
            "🔍 3. Technical Search",
            "📊 4. Architectural Summary",
            "🧩 5. SWC & Port Extraction",
            "⚠️ 6. Inconsistency & Safety",
            "🔄 7. Revision Comparator",
            "📥 8. Export Center",
        ],
        index=0,
    )

    st.divider()
    # Responsible AI & Grounding Guidelines
    with st.expander("🛡️ Responsible AI Disclaimers", expanded=False):
        st.caption("""
        - **Grounding Guarantee:** Answers cite exact pages and filenames.
        - **No Blind Approvals:** Candidate extractions require engineer verification.
        - **Untrusted Input Defense:** PDF text treated strictly as inert data.
        """)

# Fetch current documents
documents = api_client.list_documents()
doc_options = {d["id"]: f"{d['filename']} ({d['page_count']} pages)" for d in documents}
all_doc_ids = list(doc_options.keys())

# Header
col_title, col_stat = st.columns([3, 1])
with col_title:
    st.markdown('<p class="main-header">🚗 Automotive Engineering AI Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AUTOSAR High-Level Design (HLD) Document Analysis & Intelligence Platform</p>', unsafe_allow_html=True)
with col_stat:
    st.metric("Indexed Documents", len(documents))

st.divider()

# -------------------------------------------------------------
# PAGE 1: DOCUMENT LIBRARY & UPLOAD
# -------------------------------------------------------------
if nav_choice.startswith("📂 1."):
    st.subheader("Document Ingestion & Repository Management")
    st.write("Upload AUTOSAR High-Level Design PDFs or quickly load built-in sample HLD specifications.")

    # Quick Load Samples Row
    sample_dir = settings.BASE_DIR / "sample_data"
    sample_files = list(sample_dir.glob("*.pdf"))

    if sample_files:
        st.markdown("#### ⚡ Quick-Load Synthetic Automotive HLD Benchmarks")
        cols = st.columns(len(sample_files))
        for idx, sfile in enumerate(sample_files):
            with cols[idx]:
                if st.button(f"📥 Load `{sfile.name}`", key=f"quick_{idx}", use_container_width=True):
                    with st.spinner(f"Ingesting and indexing {sfile.name}..."):
                        b, name = load_sample_file(sfile)
                        res = api_client.upload_document(
                            file_bytes=b,
                            filename=name,
                            domain="Powertrain" if "Powertrain" in name else "Body Gateway",
                            version_tag="v2.0" if "v2.0" in name else "v1.0",
                        )
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.success(f"{res.get('message', 'Uploaded successfully!')}")
                            st.rerun()

    st.markdown("---")

    # File Upload Form
    uploaded_files = st.file_uploader(
        "Upload Custom AUTOSAR HLD PDF Documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload standard PDF architecture documents up to 50MB.",
    )

    col_meta1, col_meta2, col_up = st.columns([1, 1, 1])
    with col_meta1:
        domain_tag = st.selectbox("Subsystem Domain", ["Powertrain", "Body Gateway", "Chassis", "ADAS", "Infotainment"])
    with col_meta2:
        ver_tag = st.text_input("Version Tag", value="v1.0")
    with col_up:
        st.write("")
        st.write("")
        upload_btn = st.button("🚀 Process & Index Files", type="primary", use_container_width=True)

    if upload_btn and uploaded_files:
        for u_file in uploaded_files:
            file_bytes = u_file.read()
            with st.spinner(f"Validating, chunking, and embedding {u_file.name}..."):
                res = api_client.upload_document(
                    file_bytes=file_bytes,
                    filename=u_file.name,
                    domain=domain_tag,
                    version_tag=ver_tag,
                )
                if "error" in res:
                    st.error(f"Error on {u_file.name}: {res['error']}")
                elif res.get("is_duplicate"):
                    st.warning(f"⚠️ Duplicate detected: {u_file.name} is already indexed.")
                else:
                    st.success(f"✅ {u_file.name} processed and indexed successfully!")
        st.rerun()

    # Document Table
    st.markdown("### 📚 Indexed Document Repository")
    if not documents:
        st.info("No documents indexed yet. Upload a PDF or click 'Quick-Load' above to begin.")
    else:
        df_docs = pd.DataFrame([
            {
                "ID": d["id"][:8] + "...",
                "Filename": d["filename"],
                "Domain": d.get("domain", "Automotive"),
                "Version": d.get("version_tag", "v1.0"),
                "Pages": d["page_count"],
                "Size (KB)": round(d["file_size_bytes"] / 1024, 1),
                "Status": d["status"].upper(),
                "OCR Warning": "⚠️ Scanned" if d.get("ocr_warning") else "Normal",
                "full_id": d["id"],
            }
            for d in documents
        ])
        st.dataframe(df_docs.drop(columns=["full_id"]), use_container_width=True)

        # Deletion & Re-indexing Management
        st.markdown("#### Document Controls")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            sel_doc_id = st.selectbox(
                "Select Document to Manage",
                options=all_doc_ids,
                format_func=lambda x: doc_options.get(x, x),
            )
        with c2:
            if st.button("🔄 Re-Index", use_container_width=True):
                with st.spinner("Re-indexing document..."):
                    res = api_client.reindex_document(sel_doc_id)
                    st.success(f"Re-indexed {res.get('chunks_indexed', 0)} chunks.")
                    st.rerun()
        with c3:
            if st.button("🗑️ Delete Document", type="primary", use_container_width=True):
                with st.spinner("Deleting document and vector records..."):
                    if api_client.delete_document(sel_doc_id):
                        st.success("Document deleted.")
                        st.rerun()


# -------------------------------------------------------------
# PAGE 2: GROUNDED Q&A ASSISTANT (RAG)
# -------------------------------------------------------------
elif nav_choice.startswith("💬 2."):
    st.subheader("Grounded AUTOSAR Q&A Assistant")
    st.write("Ask architectural questions. All answers are strictly grounded in retrieved document evidence with page citations.")

    if not documents:
        st.warning("Please upload or quick-load a document first from 'Document Library'.")
    else:
        col_flt1, col_flt2 = st.columns([2, 1])
        with col_flt1:
            target_doc_id = st.selectbox(
                "Filter Query to Document (Optional)",
                options=["All Indexed Documents"] + all_doc_ids,
                format_func=lambda x: "All Indexed Documents" if x == "All Indexed Documents" else doc_options.get(x, x),
            )
        with col_flt2:
            top_k_val = st.slider("Retrieval Depth (Top-k Chunks)", min_value=2, max_value=8, value=4)

        # 10 realistic preset evaluation questions
        st.markdown("##### 💡 Suggested Automotive Architecture Questions:")
        preset_questions = [
            "What software components (SWCs) are defined in the Powertrain controller architecture?",
            "What are the ports and interfaces of TorqueArbitrationSWC?",
            "What is the periodic execution rate (cycle time) of TorqueArbitrationSWC?",
            "What functional safety ASIL level is allocated to the torque arbitration function?",
            "What CAN frame ID and cycle time are used for CAN_Powertrain_TorqueDemand?",
            "What E2E protection profile is configured for powertrain CAN signals?",
            "How does ThrottleActuatorSWC handle actuator faults or DTCs?",
            "What diagnostic services (UDS / DID) are supported?",
            "What is the difference between Powertrain v1.0 and v2.0?",
            "What is the battery chemistry specification of the high-voltage pack?",  # Missing info test!
        ]

        preset_sel = st.selectbox("Choose a sample question to test:", ["(Select a question...)"] + preset_questions)

        user_query = st.text_area(
            "Enter your technical question:",
            value=preset_sel if preset_sel != "(Select a question...)" else "",
            height=80,
            placeholder="e.g. Which software component is responsible for arbitrating torque demand?",
        )

        ask_btn = st.button("🔍 Ask Engineering Assistant", type="primary")

        if ask_btn and user_query:
            filter_id = None if target_doc_id == "All Indexed Documents" else target_doc_id
            with st.spinner("Retrieving evidence and synthesizing grounded response..."):
                response = api_client.ask_chat(question=user_query, document_id=filter_id, top_k=top_k_val)

            st.markdown("### 📋 Evidence-Grounded Answer")

            # Provider & Status pill
            if response.get("is_retrieval_only"):
                st.info("ℹ️ Answer generated in **Retrieval-Only Mode** (Zero API keys required). Evidence passages are extracted directly from vector chunks.")
            else:
                st.caption(f"Generated via: `{response.get('provider')}` ({response.get('model')})")

            if response.get("privacy_notice"):
                st.warning(f"🔒 {response.get('privacy_notice')}")

            # Answer Text
            st.markdown(response.get("answer", "No answer generated."))

            # Citations List
            citations = response.get("citations", [])
            if citations:
                st.markdown("##### 📌 Verified Citations:")
                pills_html = "".join([f'<span class="citation-pill">{c["citation_str"]}</span>' for c in citations])
                st.markdown(pills_html, unsafe_allow_html=True)

            # Insufficient evidence flag
            if not response.get("evidence_sufficient", True):
                st.warning("⚠️ **Groundedness Note:** The retrieved documents did not contain sufficient evidence to fully address this query.")

            # Expandable Evidence Inspector
            chunks = response.get("evidence_chunks", [])
            with st.expander(f"🔍 Inspect Retrieved Evidence Snippets ({len(chunks)} chunks)", expanded=False):
                for idx, ch in enumerate(chunks, 1):
                    st.markdown(f"""
                    <div class="evidence-box">
                        <strong>Snippet #{idx}</strong> — <code>{ch['filename']}</code> (Page {ch['page_number']}) | 
                        <em>Relevance Score: {int(ch.get('score', 0) * 100)}%</em><br/>
                        <pre style="white-space: pre-wrap; font-size: 0.85rem; margin-top: 6px;">{ch['text']}</pre>
                    </div>
                    """, unsafe_allow_html=True)


# -------------------------------------------------------------
# PAGE 3: TECHNICAL TERM SEARCH
# -------------------------------------------------------------
elif nav_choice.startswith("🔍 3."):
    st.subheader("Automotive Technical Term & Passage Search")
    st.write("Search indexed HLD documents for AUTOSAR APIs, signals, DTCs, and identifiers.")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input("Enter search query or identifier:", value="Rte_Write_")
    with col_s2:
        top_k_search = st.slider("Results limit", 2, 15, 6)

    if st.button("Search Knowledge Base", type="primary") and search_query:
        with st.spinner("Searching passages..."):
            results = api_client.search_term(query=search_query, top_k=top_k_search)

        st.markdown(f"**Found {len(results)} relevant passages for:** `{search_query}`")
        for i, r in enumerate(results, 1):
            score_pct = int(r.get("score", 0.0) * 100)
            with st.container():
                st.markdown(f"#### #{i} [Doc: `{r['filename']}`, Page: {r['page_number']}] — *Match Score: {score_pct}%*")
                st.markdown(f"```text\n{r['text']}\n```")
                st.divider()


# -------------------------------------------------------------
# PAGE 4: ARCHITECTURAL SUMMARY
# -------------------------------------------------------------
elif nav_choice.startswith("📊 4."):
    st.subheader("Architectural Document Summarizer")
    st.write("Generate an executive architectural summary, domain decomposition, and key topic breakdown.")

    if not documents:
        st.warning("Please upload or quick-load a document first.")
    else:
        sel_doc_id = st.selectbox(
            "Select Document to Summarize",
            options=all_doc_ids,
            format_func=lambda x: doc_options.get(x, x),
        )
        selected_doc = next(d for d in documents if d["id"] == sel_doc_id)

        if st.button("Generate Architectural Summary", type="primary"):
            with st.spinner("Extracting architectural domains and synthesizing summary..."):
                res = api_client.get_summary(
                    document_id=sel_doc_id,
                    filename=selected_doc["filename"],
                    page_count=selected_doc["page_count"],
                )
                st.session_state["summary_result"] = res

        if "summary_result" in st.session_state:
            res = st.session_state["summary_result"]
            st.markdown(res.get("summary_markdown", ""))

            topics = res.get("major_topics", [])
            if topics:
                st.markdown("### 🧭 Detected Architectural Topics")
                df_top = pd.DataFrame(topics)
                st.dataframe(df_top, use_container_width=True)


# -------------------------------------------------------------
# PAGE 5: SWC & PORT EXTRACTION
# -------------------------------------------------------------
elif nav_choice.startswith("🧩 5."):
    st.subheader("Software Component (SWC) & Port Interface Extraction")
    st.write("Extract candidate AUTOSAR Software Components, Provided/Required Ports, Interfaces, and ASIL allocations.")

    if not documents:
        st.warning("Please upload or quick-load a document first.")
    else:
        sel_doc_id = st.selectbox(
            "Select Document for Component Extraction",
            options=all_doc_ids,
            format_func=lambda x: doc_options.get(x, x),
        )
        selected_doc = next(d for d in documents if d["id"] == sel_doc_id)

        if st.button("Extract Components & Ports", type="primary"):
            with st.spinner("Parsing AUTOSAR architecture taxonomy..."):
                res = api_client.extract_components(document_id=sel_doc_id, filename=selected_doc["filename"])
                st.session_state["extracted_components"] = res

        if "extracted_components" in st.session_state:
            res = st.session_state["extracted_components"]
            st.markdown(f"**Found {res.get('component_count', 0)} Candidate Components**")
            st.caption(f"Extraction Method: `{res.get('extraction_method')}`")
            st.info(f"Status: **{res.get('status_notice')}**", icon="⚠️")

            for c in res.get("components", []):
                with st.expander(f"📦 {c.get('name')} ({c.get('component_type')}) — {c.get('cycle_time_ms')} | {c.get('asil_level')}", expanded=True):
                    st.markdown(f"- **Component Type:** `{c.get('component_type')}`")
                    st.markdown(f"- **Execution Period:** `{c.get('cycle_time_ms')}`")
                    st.markdown(f"- **Safety Level:** `{c.get('asil_level')}`")
                    st.markdown(f"- **Citation:** `{c.get('citation')}`")

                    ports = c.get("ports", [])
                    if ports:
                        st.markdown("**Configured Ports:**")
                        df_p = pd.DataFrame([
                            {
                                "Port Name": p.get("name"),
                                "Type": p.get("port_type"),
                                "Interface": p.get("interface"),
                                "Citation": p.get("citation"),
                            }
                            for p in ports
                        ])
                        st.dataframe(df_p, use_container_width=True)
                    else:
                        st.caption("No explicit ports extracted for this component block.")


# -------------------------------------------------------------
# PAGE 6: INCONSISTENCY & SAFETY CHECKS
# -------------------------------------------------------------
elif nav_choice.startswith("⚠️ 6."):
    st.subheader("Architectural Inconsistency & Safety Boundary Analyzer")
    st.write("Detect potential unmapped ports, timing sampling rate conflicts, and ISO 26262 ASIL boundaries.")

    if not documents:
        st.warning("Please upload or quick-load a document first.")
    else:
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            doc_1 = st.selectbox(
                "Primary Document",
                options=all_doc_ids,
                format_func=lambda x: doc_options.get(x, x),
                key="inc_doc_1",
            )
        with col_i2:
            sec_doc_ids = ["None (Single Document Analysis)"] + [d for d in all_doc_ids if d != doc_1]
            doc_2 = st.selectbox(
                "Secondary Document (Optional Cross-ECU Check)",
                options=sec_doc_ids,
                format_func=lambda x: "None (Single Document Analysis)" if x.startswith("None") else doc_options.get(x, x),
                key="inc_doc_2",
            )

        if st.button("Run Inconsistency Analysis", type="primary"):
            with st.spinner("Analyzing port bindings, cycle times, and safety boundaries..."):
                sec_id = None if doc_2.startswith("None") else doc_2
                selected_doc = next(d for d in documents if d["id"] == doc_1)
                res = api_client.detect_inconsistencies(
                    document_id=doc_1,
                    filename=selected_doc["filename"],
                    sec_doc_id=sec_id,
                )
                st.session_state["inconsistency_res"] = res

        if "inconsistency_res" in st.session_state:
            res = st.session_state["inconsistency_res"]
            st.markdown(f"### Findings ({res.get('findings_count', 0)})")
            st.warning(res.get("compliance_disclaimer"), icon="ℹ️")

            for f in res.get("findings", []):
                sev = f.get("severity", "Medium")
                icon = "🔴" if sev == "High" else "🟡" if sev == "Medium" else "🔵"
                with st.expander(f"{icon} [{f.get('category')}] {f.get('title')}", expanded=True):
                    st.markdown(f"**Affected SWC:** `{f.get('affected_swc')}`")
                    st.markdown(f"**Details:** {f.get('details')}")
                    st.markdown(f"**Verification Label:** `{f.get('verification_label')}`")
                    st.markdown(f"**Evidence Citation:** `{f.get('evidence_citation')}`")


# -------------------------------------------------------------
# PAGE 7: REVISION COMPARATOR
# -------------------------------------------------------------
elif nav_choice.startswith("🔄 7."):
    st.subheader("Document Revision & Architectural Comparator")
    st.write("Compare two document versions (e.g. v1.0 vs v2.0) to highlight added, removed, and modified components.")

    if len(documents) < 2:
        st.warning("Please upload or quick-load at least two documents to perform a comparison (e.g. Powertrain v1.0 and v2.0).")
    else:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            doc_a_id = st.selectbox(
                "Base Document (Version A)",
                options=all_doc_ids,
                format_func=lambda x: doc_options.get(x, x),
                key="cmp_doc_a",
            )
        with col_c2:
            remaining = [d for d in all_doc_ids if d != doc_a_id]
            doc_b_id = st.selectbox(
                "Target Document (Version B)",
                options=remaining if remaining else all_doc_ids,
                format_func=lambda x: doc_options.get(x, x),
                key="cmp_doc_b",
            )

        if st.button("Execute Architectural Comparison", type="primary"):
            with st.spinner("Comparing components, ports, cycle times, and ASIL allocations..."):
                doc_a_name = next(d["filename"] for d in documents if d["id"] == doc_a_id)
                doc_b_name = next(d["filename"] for d in documents if d["id"] == doc_b_id)
                res = api_client.compare_documents(
                    doc_a_id=doc_a_id,
                    doc_a_name=doc_a_name,
                    doc_b_id=doc_b_id,
                    doc_b_name=doc_b_name,
                )
                st.session_state["compare_res"] = res

        if "compare_res" in st.session_state:
            res = st.session_state["compare_res"]
            s = res.get("summary", {})

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Added Components", s.get("added_count", 0))
            col_m2.metric("Removed Components", s.get("removed_count", 0))
            col_m3.metric("Modified Components", s.get("modified_count", 0))
            col_m4.metric("Unchanged", s.get("unchanged_count", 0))

            st.caption(f"Verification Note: {res.get('verification_note')}")

            # Added
            st.markdown("#### 🟢 Added Components in Target Document")
            added = res.get("added_components", [])
            if added:
                for a in added:
                    st.success(f"**+ `{a['component_name']}`** ({a.get('type')}) | Cycle: `{a.get('cycle_time')}` | ASIL: `{a.get('asil')}`\n\n*Impact:* {a.get('engineering_impact')}\n\n*Citation:* {a.get('citation')}")
            else:
                st.write("*No components added.*")

            # Modified
            st.markdown("#### 🟡 Modified Components")
            modified = res.get("modified_components", [])
            if modified:
                for m in modified:
                    with st.expander(f"~ `{m['component_name']}` Changes", expanded=True):
                        for chg in m.get("changes", []):
                            st.write(f"- {chg}")
                        st.info(f"Engineering Impact: {m.get('engineering_impact')}")
                        st.caption(f"Doc A: {m.get('doc_a_citation')} | Doc B: {m.get('doc_b_citation')}")
            else:
                st.write("*No modified components detected.*")

            # Removed
            st.markdown("#### 🔴 Removed Components")
            removed = res.get("removed_components", [])
            if removed:
                for r in removed:
                    st.error(f"- `{r['component_name']}` ({r.get('type')})\n\n*Impact:* {r.get('engineering_impact')}")
            else:
                st.write("*No components removed.*")


# -------------------------------------------------------------
# PAGE 8: EXPORT CENTER
# -------------------------------------------------------------
elif nav_choice.startswith("📥 8."):
    st.subheader("Analysis Export Center")
    st.write("Export structured summaries, extracted components, and findings to CSV, JSON, or Markdown.")

    if not documents:
        st.warning("Please upload or quick-load a document first.")
    else:
        sel_doc_id = st.selectbox(
            "Select Document to Export",
            options=all_doc_ids,
            format_func=lambda x: doc_options.get(x, x),
            key="export_doc_sel",
        )
        selected_doc = next(d for d in documents if d["id"] == sel_doc_id)

        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            st.markdown("##### 📄 Export Components (CSV)")
            if st.button("Generate Components CSV"):
                comp_data = api_client.extract_components(sel_doc_id, selected_doc["filename"])
                csv_str = analysis_exporter.export_components_csv(comp_data)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_str,
                    file_name=f"{selected_doc['filename']}_components.csv",
                    mime="text/csv",
                )

        with col_e2:
            st.markdown("##### ⚠️ Export Inconsistencies (CSV)")
            if st.button("Generate Findings CSV"):
                inc_data = api_client.detect_inconsistencies(sel_doc_id, selected_doc["filename"])
                csv_str = analysis_exporter.export_inconsistencies_csv(inc_data)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_str,
                    file_name=f"{selected_doc['filename']}_inconsistencies.csv",
                    mime="text/csv",
                )

        with col_e3:
            st.markdown("##### 📊 Export Full JSON")
            if st.button("Generate Complete JSON"):
                comp_data = api_client.extract_components(sel_doc_id, selected_doc["filename"])
                json_str = analysis_exporter.export_json(comp_data)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=f"{selected_doc['filename']}_analysis.json",
                    mime="application/json",
                )
