from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
import os

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

os.environ["OPENAI_API_KEY"] = ""

db1 = FAISS.from_texts(["foo"], embeddings)
db2 = FAISS.from_texts(["bar"], embeddings)

db1.merge_from(db2)

print(db1.docstore._dict)