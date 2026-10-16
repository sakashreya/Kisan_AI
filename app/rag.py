import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import glob

import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterCondition
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from .config import CHROMA_PATH, EMBED_MODEL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PDF_DIR = os.path.join(ROOT, "data", "pdfs")
CHROMA_ABS = CHROMA_PATH if os.path.isabs(CHROMA_PATH) else os.path.join(ROOT, CHROMA_PATH)

# e5 models need these prefixes for good retrieval quality
Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBED_MODEL, query_instruction="query: ", text_instruction="passage: "
)
Settings.llm = None  # retrieval only; the agent LLM writes the answer
Settings.node_parser = SentenceSplitter(chunk_size=800, chunk_overlap=120)

ALIASES = {"paddy": "rice", "red gram": "tur", "pigeon pea": "tur", "arhar": "tur",
           "gram": "chickpea", "bengal gram": "chickpea", "chana": "chickpea",
           "soyabean": "soybean", "groundnut": "groundnut", "peanut": "groundnut",
           "corn": "maize", "capsicum": "chilli", "brinjal": "brinjal", "eggplant": "brinjal"}

EXCLUDED_SOURCES = {
    "rice__fao_integrated_crop_management.pdf",
}

_vs = None
_col = None
_crop_keys_cache = None


def collection():
    global _col
    if _col is None:
        _col = chromadb.PersistentClient(path=CHROMA_ABS).get_or_create_collection("icar")
    return _col


def vector_store():
    global _vs
    if _vs is None:
        _vs = ChromaVectorStore(chroma_collection=collection())
    return _vs


def crop_from_filename(path: str) -> str:
    """'rice__fao_handbook.pdf' -> 'rice'. 'multi__...' = covers many crops."""
    name = os.path.basename(path)
    return name.split("__")[0].lower() if "__" in name else "multi"


def already_ingested(source: str) -> bool:
    try:
        return len(collection().get(where={"source": source}, limit=1)["ids"]) > 0
    except Exception:
        return False


def ingest(pdf_dir: str = DEFAULT_PDF_DIR):
    files = sorted(glob.glob(os.path.join(pdf_dir, "**", "*.pdf"), recursive=True)
                   + glob.glob(os.path.join(pdf_dir, "**", "*.txt"), recursive=True))
    if not files:
        raise SystemExit(f"No PDFs found in {pdf_dir}. Run scripts/download_data.py or add files "
                         "named like  rice__source_name.pdf")
    ctx = StorageContext.from_defaults(vector_store=vector_store())
    done = skipped = 0
    for f in files:
        name = os.path.basename(f)
        if already_ingested(name):
            print(f"skip (already ingested): {name}")
            skipped += 1
            continue
        try:
            from llama_index.readers.file import PDFReader
            docs = SimpleDirectoryReader(
                input_files=[f], file_extractor={".pdf": PDFReader()}
            ).load_data()
        except Exception as e:
            print(f"FAILED to read {name}: {e}")
            continue
        docs =[d for d in docs if d.text and d.text.strip()
                and "endobj" not in d.text[:2000] and not d.text.lstrip().startswith("%PDF")]
        if not docs:
            print(f"WARNING: {name} has no extractable text (scanned PDF?). Needs OCR. Skipped.")
            continue
        crop = crop_from_filename(f)
        for d in docs:
            d.metadata = {"source": name, "crop": crop, "page": d.metadata.get("page_label", "?")}
            d.excluded_embed_metadata_keys = ["source", "page"]
            d.excluded_llm_metadata_keys = []
        print(f"ingesting {name}  crop={crop}  pages={len(docs)}")
        VectorStoreIndex.from_documents(docs, storage_context=ctx, show_progress=True)
        done += 1
    global _crop_keys_cache
    _crop_keys_cache = None
    print(f"Finished. ingested={done} skipped={skipped} total chunks={collection().count()}")


def get_crop_keys() -> list[str]:
    global _crop_keys_cache
    if _crop_keys_cache is None:
        metas = collection().get(include=["metadatas"])["metadatas"]
        _crop_keys_cache = sorted({m.get("crop", "?") for m in metas if m and m.get("crop")})
    return _crop_keys_cache


def list_crops() -> list[str]:
    return get_crop_keys()


def search(query: str, crop: str | None = None, k: int = 5) -> str:
    index = VectorStoreIndex.from_vector_store(vector_store())
    crop = (crop or "").strip().lower()
    crop = ALIASES.get(crop, crop)
    fetch_k = k + 15
    nodes = []
    if crop:
        all_crops = get_crop_keys()
        matching_crops = {c for c in all_crops if c == crop or c.startswith(f"{crop}_")}
        if matching_crops:
            flt = MetadataFilters(
                filters=[MetadataFilter(key="crop", value=c_name) for c_name in sorted(matching_crops)],
                condition=FilterCondition.OR,
            )
            retrieved = index.as_retriever(similarity_top_k=fetch_k, filters=flt).retrieve(query)
            nodes = [n for n in retrieved if n.node.metadata.get("source") not in EXCLUDED_SOURCES]
            if len(nodes) < k and len(retrieved) == fetch_k:
                retrieved = index.as_retriever(similarity_top_k=k + 35, filters=flt).retrieve(query)
                nodes = [n for n in retrieved if n.node.metadata.get("source") not in EXCLUDED_SOURCES]
    if not nodes:  # unknown crop or nothing found: search everything
        retrieved = index.as_retriever(similarity_top_k=fetch_k).retrieve(query)
        nodes = [n for n in retrieved if n.node.metadata.get("source") not in EXCLUDED_SOURCES]
        if len(nodes) < k and len(retrieved) == fetch_k:
            retrieved = index.as_retriever(similarity_top_k=k + 35).retrieve(query)
            nodes = [n for n in retrieved if n.node.metadata.get("source") not in EXCLUDED_SOURCES]
    nodes = nodes[:k]
    if not nodes:
        return "No relevant information found in the knowledge base."
    parts = []
    for n in nodes:
        m = n.node.metadata
        parts.append(f"[source: {m.get('source', '?')} | crop: {m.get('crop', '?')} | "
                     f"page {m.get('page', '?')}] {n.node.get_content()[:1200]}")
    return "\n\n".join(parts)
