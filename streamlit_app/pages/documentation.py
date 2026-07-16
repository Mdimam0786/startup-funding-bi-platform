"""Documentation page: browse, search across, and download every written
report from the project (data dictionary, glossary, EDA/stats/ML reports)."""
import io
import sys
import zipfile
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.docs_loader import load_all_docs, search_docs, DOC_REGISTRY
from utils.error_handler import safe_run


def render_header():
    st.markdown(
    """
    <div class="pill pill-static"><span class="pill-dot"></span> 8 documents · same source files as the GitHub repository</div>
    <div style="height:0.5rem"></div>
    <h1 style="margin-bottom:0.1rem;">Documentation</h1>
    """,
    unsafe_allow_html=True,
)

st.caption("Project documentation by Md Imamuddin")

st.markdown(
    """
    <p class="subtle" style="margin-top:0;">
    Browse, search, and download all project documentation, including data
    engineering, SQL, exploratory analysis, statistics, machine learning,
    and business reports.
    </p>
    """,
    unsafe_allow_html=True,
)

@safe_run("Couldn't render the document search.")
def render_search(docs: dict):
    query = st.text_input("Search all documentation", placeholder="e.g. \"heteroscedasticity\", \"unicorn match rate\", \"star schema\"")
    if not query:
        return None

    results = search_docs(docs, query)
    if not results:
        st.info(f"No matches for \"{query}\".")
        return None

    st.markdown(f'<p class="subtle" style="font-size:0.83rem;">{len(results)} document(s) contain "{query}":</p>', unsafe_allow_html=True)
    for key, doc, matches in results:
        with st.expander(f"{doc['icon']} {doc['title']} — {len(matches)} match(es) shown"):
            for m in matches:
                st.markdown(f"> {m}")
            if st.button(f"Open {doc['title']}", key=f"open_{key}"):
                st.session_state["selected_doc"] = key
                st.rerun()
    return results


def render_doc_grid(docs: dict):
    st.markdown("### All Documents")
    cols = st.columns(4)
    keys = list(DOC_REGISTRY.keys())
    for i, key in enumerate(keys):
        doc = docs[key]
        with cols[i % 4]:
            clicked = st.button(
                f"{doc['icon']}  {doc['title']}",
                key=f"select_{key}", use_container_width=True,
            )
            st.markdown(f'<p class="subtle" style="font-size:0.75rem; margin-top:-0.6rem; margin-bottom:0.8rem;">{doc["description"]}</p>', unsafe_allow_html=True)
            if clicked:
                st.session_state["selected_doc"] = key
                st.rerun()


@safe_run("Couldn't render the selected document.")
def render_selected_doc(docs: dict):
    selected_key = st.session_state.get("selected_doc", "project_report")
    doc = docs[selected_key]

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""<div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin:0;">{doc['icon']} {doc['title']}</h3>
        </div>""",
        unsafe_allow_html=True,
    )

    st.download_button(
        f"⬇ Download {doc['title']} (.md)", data=doc["content"].encode("utf-8"),
        file_name=DOC_REGISTRY[selected_key]["file"], mime="text/markdown", key=f"dl_{selected_key}",
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(doc["content"])


def render_download_all(docs: dict):
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for key, doc in docs.items():
            zf.writestr(DOC_REGISTRY[key]["file"], doc["content"])
    buffer.seek(0)

    st.download_button(
        "⬇ Download all documentation (.zip)",
        data=buffer, file_name="project_documentation.zip", mime="application/zip",
    )


def render():
    render_header()
    docs = load_all_docs()

    render_search(docs)
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    render_doc_grid(docs)
    render_selected_doc(docs)
    render_download_all(docs)
