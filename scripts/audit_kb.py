"""Audit the ChromaDB knowledge base against data/pdfs.

Reports:
1. Chunks per crop and per source file in ChromaDB.
2. Files in data/pdfs that are NOT in ChromaDB (not ingested).
3. Files in ChromaDB that are NOT in data/pdfs (orphaned).
4. Any chunks containing raw-PDF artefacts ("endobj", "%PDF").
5. Whether pypdf / llama-index PDF reader is importable.

Run:  python scripts/audit_kb.py
"""
import os, sys, glob, collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(ROOT, "chroma_db")
PDF_DIR = os.path.join(ROOT, "data", "pdfs")


def main():
    # --- 0. Check PDF reader ---
    print("=" * 60)
    print("0. PDF READER CHECK")
    print("=" * 60)
    try:
        from llama_index.readers.file import PDFReader
        print("  llama_index.readers.file.PDFReader  -> OK")
    except ImportError as e:
        print(f"  llama_index.readers.file.PDFReader  -> MISSING ({e})")
    try:
        import pypdf
        print(f"  pypdf version {pypdf.__version__}  -> OK")
    except ImportError:
        print("  pypdf  -> MISSING (raw PDF text may be stored!)")

    # --- 1. Open ChromaDB ---
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        col = client.get_collection("icar")
    except Exception as e:
        print(f"\nERROR: cannot open collection 'icar': {e}")
        return

    total = col.count()
    print(f"\nChromaDB collection 'icar': {total} total chunks")

    # Fetch all metadata (in batches if large)
    all_meta = []
    batch_size = 5000
    offset = 0
    while offset < total:
        result = col.get(limit=batch_size, offset=offset, include=["metadatas", "documents"])
        all_meta.extend(zip(result["ids"], result["metadatas"], result["documents"]))
        offset += batch_size

    # --- 2. Chunks per crop ---
    print("\n" + "=" * 60)
    print("1. CHUNKS PER CROP")
    print("=" * 60)
    crop_counts = collections.Counter()
    source_counts = collections.Counter()
    crop_sources = collections.defaultdict(set)
    for cid, meta, doc in all_meta:
        crop = meta.get("crop", "?") if meta else "?"
        source = meta.get("source", "?") if meta else "?"
        crop_counts[crop] += 1
        source_counts[source] += 1
        crop_sources[crop].add(source)

    for crop in sorted(crop_counts):
        print(f"  {crop:20s}  {crop_counts[crop]:5d} chunks  sources: {sorted(crop_sources[crop])}")

    # --- 3. Chunks per source file ---
    print("\n" + "=" * 60)
    print("2. CHUNKS PER SOURCE FILE")
    print("=" * 60)
    for src in sorted(source_counts):
        print(f"  {src:50s}  {source_counts[src]:5d} chunks")

    # --- 4. Cross-reference with data/pdfs ---
    print("\n" + "=" * 60)
    print("3. CROSS-REFERENCE: data/pdfs vs ChromaDB")
    print("=" * 60)
    disk_files = set()
    for f in glob.glob(os.path.join(PDF_DIR, "**", "*.*"), recursive=True):
        disk_files.add(os.path.basename(f))

    chroma_sources = set(source_counts.keys())

    not_ingested = disk_files - chroma_sources
    orphaned = chroma_sources - disk_files

    print(f"\n  Files on disk: {len(disk_files)}")
    print(f"  Sources in ChromaDB: {len(chroma_sources)}")

    if not_ingested:
        print(f"\n  NOT INGESTED (on disk but not in ChromaDB): {len(not_ingested)}")
        for f in sorted(not_ingested):
            print(f"    - {f}")
    else:
        print("\n  All disk files are ingested.")

    if orphaned:
        print(f"\n  ORPHANED (in ChromaDB but not on disk): {len(orphaned)}")
        for f in sorted(orphaned):
            print(f"    - {f}")
    else:
        print("\n  No orphaned entries in ChromaDB.")

    # --- 5. Raw-PDF artefact check ---
    print("\n" + "=" * 60)
    print("4. RAW-PDF ARTEFACT CHECK (endobj / %PDF)")
    print("=" * 60)
    bad_chunks = []
    for cid, meta, doc in all_meta:
        if doc and ("endobj" in doc[:2000] or doc.lstrip().startswith("%PDF")):
            source = meta.get("source", "?") if meta else "?"
            bad_chunks.append((cid, source, doc[:120].replace("\n", " ")))

    if bad_chunks:
        print(f"  FOUND {len(bad_chunks)} chunks with raw-PDF artefacts:")
        for cid, src, preview in bad_chunks[:20]:
            print(f"    [{src}] id={cid}: {preview}...")
        if len(bad_chunks) > 20:
            print(f"    ... and {len(bad_chunks) - 20} more")
    else:
        print("  No raw-PDF artefacts found. All chunks look clean.")

    # --- 6. Flag Myanmar / FAO rice content ---
    print("\n" + "=" * 60)
    print("5. MYANMAR / FAO RICE CHECK")
    print("=" * 60)
    myanmar_chunks = []
    for cid, meta, doc in all_meta:
        if doc and "myanmar" in doc.lower():
            source = meta.get("source", "?") if meta else "?"
            myanmar_chunks.append((cid, source))

    if myanmar_chunks:
        sources_with_myanmar = collections.Counter(s for _, s in myanmar_chunks)
        print(f"  FOUND {len(myanmar_chunks)} chunks mentioning 'myanmar':")
        for src, cnt in sources_with_myanmar.most_common():
            print(f"    {src}: {cnt} chunks")
    else:
        print("  No chunks mentioning 'myanmar'.")

    # Check if the FAO rice file exists on disk
    fao_file = os.path.join(PDF_DIR, "rice__fao_integrated_crop_management.pdf")
    if os.path.exists(fao_file):
        size_mb = os.path.getsize(fao_file) / 1e6
        print(f"\n  FILE EXISTS: rice__fao_integrated_crop_management.pdf ({size_mb:.1f} MB)")
        print("  ACTION NEEDED: This file describes Myanmar rice farming and should be removed.")
    else:
        print("\n  rice__fao_integrated_crop_management.pdf is NOT on disk.")

    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
