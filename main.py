import os

import numpy as np
import rdflib
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
import faiss
import time
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader


def find_uri(ontology):
    for ns_prefix, namespace in ontology.namespaces():
        if not ns_prefix:
            return namespace
    return ""


os.environ["OPENAI_API_KEY"] = ""

# o1 = rdflib.Graph().parse("cmt-conference/component/source.xml", format="xml")
# o2 = rdflib.Graph().parse("cmt-conference/component/target.xml", format="xml")
# o1_base_iri = find_uri(o1)
# o2_base_iri = find_uri(o2)
# l1 = len(o1_base_iri)
# l2 = len(o2_base_iri)

# for triple in o1:
#     subject = str(triple[0])[l1:]
#     print(subject)
#     predicate = str(triple[1])
#     obj = str(triple[2])

# loader = PyPDFLoader("Brick.pdf")
# data = loader.load()

reader = PdfReader('Brick.pdf')
page = reader.pages[0]

# extracting text from page
data = page.extract_text()
# print(data)


# text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
# docs = text_splitter.split_documents(documents)
# embeddings = OpenAIEmbeddings()
# db = FAISS.from_documents(docs, embeddings)

model = SentenceTransformer('distilbert-base-nli-mean-tokens')
encoded_data = model.encode(data)

index = faiss.IndexIDMap(faiss.IndexFlatIP(768))
# index.add_with_ids(encoded_data, np.array(range(0, len(data))))

faiss.write_index(index, 'abc_news')
index = faiss.read_index('abc_news')


def search(query):
    t = time.time()
    query_vector = model.encode([query])
    k = 5
    top_k = index.search(query_vector, k)
    print('totaltime: {}'.format(time.time() - t))
    return [data[_id] for _id in top_k[1].tolist()[0]]


query = str("what is Brick Schema?")
results = search(query)
print('results :')
for result in results:
    print('\t', result)

# docs = db.similarity_search(query)
# print(docs[0].page_content)

# docs_and_scores = db.similarity_search_with_score(query)
# print(docs_and_scores[0])
