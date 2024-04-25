import os
import dotenv
from langchain.retrievers import WebResearchRetriever
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models.openai import ChatOpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.chains.question_answering import load_qa_chain
import rag

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# file path
o1_path = "../data/conference/cmt-conference/component/source.xml"
o2_path = "../data/conference/cmt-conference/component/target.xml"
align_path = "../data/conference/cmt-conference/component/reference.xml"
predict_path = "predict_target.csv"
true_path = "true.csv"

# find all entities
e1_list_class, e2_list_class, e1_list_property, e2_list_property = rag.find_all_entities(o1_path, o2_path)

# Vectorstore
vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")

# LLM
llm = ChatOpenAI(temperature=0)

# Search
search = GoogleSearchAPIWrapper()
web_research_retriever = WebResearchRetriever.from_llm(
    vectorstore=vectorstore,
    llm=llm,
    search=search,
)

with open('rag/lexical.txt', 'w') as f:
    # for e in e1_list_class + e2_list_class + e1_list_property + e2_list_property:
    #     user_input = "What is meaning of " + e.split(":")[-1] + " in the context of conference?"
    #     print("user_input:", user_input)
    #     useful_doc = web_research_retriever.get_relevant_documents(user_input)
    #     chain = load_qa_chain(llm, chain_type="stuff")
    #     output = chain({"input_documents": useful_doc, "question": user_input}, return_only_outputs=True)
    #     text = output['output_text']
    #     print("output:", text)
    #     f.write("%s means %s." % (e, text))
    #     f.write('\n')
    user_input = "What is meaning of Chairman in the context of conference?"
    print("user_input:", user_input)
    docs = web_research_retriever.get_relevant_documents(user_input)
    chain = load_qa_chain(llm, chain_type="stuff")
    output = chain({"input_documents": docs, "question": user_input}, return_only_outputs=True)
    text = output['output_text']
    print("output:", text)
    f.write("%s means %s." % ("cmt:Chairman", text))
    f.write('\n')
    user_input = "What is meaning of Chair in the context of conference?"
    print("user_input:", user_input)
    docs = web_research_retriever.get_relevant_documents(user_input)
    chain = load_qa_chain(llm, chain_type="stuff")
    output = chain({"input_documents": docs, "question": user_input}, return_only_outputs=True)
    text = output['output_text']
    print("output:", text)
    f.write("%s means %s." % ("conference:Chair", text))
    f.write('\n')
