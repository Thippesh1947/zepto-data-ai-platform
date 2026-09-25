import os
import chromadb
from chromadb.utils import embedding_functions

def run_ingestion():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "docs")
    db_dir = os.path.join(base_dir, "chroma_db")

    print(f"Reading policy documents from: {docs_dir}")
    doc_files = sorted([f for f in os.listdir(docs_dir) if f.startswith("doc_") and f.endswith(".txt")])
    
    if not doc_files:
        raise FileNotFoundError(f"No policy documents found in {docs_dir}")

    documents = []
    ids = []
    metadatas = []

    for filename in doc_files:
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        doc_id = os.path.splitext(filename)[0]
        documents.append(content)
        ids.append(doc_id)
        metadatas.append({"source": filename})
        print(f"Loaded {filename} (ID: {doc_id}, Length: {len(content)} chars)")

    print(f"\nInitializing ChromaDB persistent client at: {db_dir}")
    client = chromadb.PersistentClient(path=db_dir)

    print("Setting up SentenceTransformer embedding function ('all-MiniLM-L6-v2')...")
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name="zepto_policies",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"Indexing {len(documents)} policy chunks into ChromaDB collection 'zepto_policies'...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    count = collection.count()
    print(f"\n[PASSED] Ingestion complete. Total indexed chunks in 'zepto_policies': {count}")

if __name__ == "__main__":
    run_ingestion()