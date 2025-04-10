from pymongo import MongoClient
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import os

# ---------------- MongoDB Setup ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["synthetic_ehr"]
patient_col = db["patient_records"]

# ---------------- Load Data ----------------
def fetch_patient_docs():
    documents = []
    for record in patient_col.find({}):
        user_id = record.get("patient_id", "Unknown")
        text_chunks = []

        for k, v in record.items():
            if k != "_id":
                text_chunks.append(f"{k}: {v}")

        doc_text = "\n".join(text_chunks)
        documents.append(Document(page_content=doc_text, metadata={"patient_id": user_id}))
    return documents

# ---------------- FAISS Build ----------------
def build_faiss_index():
    print("Fetching documents...")
    docs = fetch_patient_docs()
    print(f"Loaded {len(docs)} patient records.")

    print("Loading embeddings...")
    embeddings = HuggingFaceEmbeddings()

    print("Building FAISS index...")
    vectorstore = FAISS.from_documents(docs, embeddings)

    print("Saving FAISS index to disk...")
    vectorstore.save_local("faiss_index")
    print("FAISS index saved to ./faiss_index")

if __name__ == "__main__":
    build_faiss_index()
