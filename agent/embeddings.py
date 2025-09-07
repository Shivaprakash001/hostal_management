# agent/embeddings.py
from langchain_huggingface import HuggingFaceEmbeddings

# ✅ Load embeddings only once
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
