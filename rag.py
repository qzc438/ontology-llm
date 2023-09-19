from operator import itemgetter
import os
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
recurSplitter = RecursiveCharacterTextSplitter(chunk_size=100,
                                               chunk_overlap=20,
                                               length_function=len)

os.environ["OPENAI_API_KEY"] = ""

with open('graphical.txt') as spc:
  txt_spc = spc.read()
graphical_docs = recurSplitter.create_documents([txt_spc])

with open('initial.txt') as init:
  txt_init = init.read()
initial_docs = recurSplitter.create_documents([txt_init])

documents = graphical_docs + initial_docs

vectorstore = FAISS.from_documents(documents, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)

model = ChatOpenAI()

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# print(chain.invoke(
#                    # "Given the source ontology property assign external reviewer. "
#                    " Given mark conflict of interest in the source ontology, what is the most similar property in the target ontology?"
#                    "Think step by step. "
#                    # "Only answer the class name. "
#                    # "Please also give a confidence score between 0 and 1 based on similarity."
#                    ))

print(chain.invoke(
                   "Given the source ontology property assign external reviewer. "
                   " Please compare the similarity of subject area in the source ontology and topic in the target ontology. "
                   "Think step by step. "
                   # "Only answer the class name. "
                   # "Please also give a confidence score between 0 and 1 based on similarity."
                   ))