"""Remove rice__fao_integrated_crop_management.pdf from disk and its chunks from ChromaDB."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(ROOT, "chroma_db")
PDF_DIR = os.path.join(ROOT, "data", "pdfs")
TARGET_SOURCE = "rice__fao_integrated_crop_management.pdf"

import chromadb

# 1. Remove chunks from ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
col = client.get_collection("icar")

print(f"ChromaDB before: {col.count()} chunks")

# Get all IDs with this source
result = col.get(where={"source": TARGET_SOURCE}, include=[])
ids_to_delete = result["ids"]
print(f"Found {len(ids_to_delete)} chunks from '{TARGET_SOURCE}'")

if ids_to_delete:
    # ChromaDB delete has a batch limit; delete in batches
    batch = 100
    for i in range(0, len(ids_to_delete), batch):
        col.delete(ids=ids_to_delete[i:i+batch])
    print(f"Deleted {len(ids_to_delete)} chunks from ChromaDB")

print(f"ChromaDB after: {col.count()} chunks")

# 2. Remove file from disk
fpath = os.path.join(PDF_DIR, TARGET_SOURCE)
if os.path.exists(fpath):
    os.remove(fpath)
    print(f"Deleted file: {fpath}")
else:
    print(f"File not found on disk: {fpath}")

print("Done.")
