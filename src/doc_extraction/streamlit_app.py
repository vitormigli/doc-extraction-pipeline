"""Streamlit demo: upload a document image, pick its type, see the extracted JSON."""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from doc_extraction.extraction import extract_document  # noqa: E402
from doc_extraction.schemas import DocumentType  # noqa: E402

st.set_page_config(page_title="Document Extraction Pipeline", page_icon="📄")
st.title("Document Extraction Pipeline")
st.caption("Upload a Brazilian document image and extract structured, validated JSON.")

doc_type = st.selectbox(
    "Document type",
    options=list(DocumentType),
    format_func=lambda d: d.value.replace("_", " ").title(),
)

uploaded = st.file_uploader("Document image", type=["png", "jpg", "jpeg"])

if uploaded and st.button("Extract"):
    st.image(uploaded, caption="Input document", use_container_width=True)

    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    with st.spinner("Extracting..."):
        result = extract_document(tmp_path, doc_type)
    tmp_path.unlink(missing_ok=True)

    if result.validated:
        st.success(
            f"Valid on {'first' if result.valid_on_first_try else 'retry'} try "
            f"({result.latency_seconds:.2f}s)"
        )
        st.json(result.validated.model_dump())
    else:
        st.error(f"Extraction failed validation: {result.error}")
        st.json(result.raw_output)
