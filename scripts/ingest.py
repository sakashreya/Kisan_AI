import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.rag import ingest, list_crops, DEFAULT_PDF_DIR

if __name__ == "__main__":
    ingest(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF_DIR)
    print("Crops in knowledge base:", list_crops())
