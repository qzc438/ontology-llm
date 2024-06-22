import os
import dotenv
import pandas as pd
import rdflib
import util
import csv
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')


def find_alignment(align_path, o1_path, o2_path, y_true_path):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # load ontologies
    o1 = rdflib.Graph().parse(o1_path)
    o2 = rdflib.Graph().parse(o2_path)
    o1_base_iri = util.find_uri(o1)
    o2_base_iri = util.find_uri(o2)
    o1_prefix = rdflib.Namespace(o1_base_iri)
    o2_prefix = rdflib.Namespace(o2_base_iri)
    o1.bind("cmt", o1_prefix)
    o2.bind("conference", o2_prefix)
    # create true csv
    util.create_document(y_true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(y_true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            e1 = o1.namespace_manager.qname(str(align.value(s, alignEntity1, None)))
            e2 = o2.namespace_manager.qname(str(align.value(s, alignEntity2, None)))
            list_pair = [e1, e2]
            writer.writerow(list_pair)


def find_all_entities(o1_path, o2_path):
    o1 = rdflib.Graph().parse(o1_path)
    o2 = rdflib.Graph().parse(o2_path)
    o1_base_iri = util.find_uri(o1)
    o2_base_iri = util.find_uri(o2)
    o1_prefix = rdflib.Namespace(o1_base_iri)
    o2_prefix = rdflib.Namespace(o2_base_iri)
    o1.bind("cmt", o1_prefix)
    o2.bind("conference", o2_prefix)
    # add entities into list
    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x and "#" in x:
            e1_list_class.append(o1.namespace_manager.qname(str(x)))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y and "#" in y:
            e2_list_class.append(o2.namespace_manager.qname(str(y)))
    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x and "#" in x:
            e1_list_property.append(o1.namespace_manager.qname(str(x)))
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x and "#" in x:
            e1_list_property.append(o1.namespace_manager.qname(str(x)))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y and "#" in y:
            e2_list_property.append(o2.namespace_manager.qname(str(y)))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y and "#" in y:
            e2_list_property.append(o2.namespace_manager.qname(str(y)))

    print("e1_list_class", e1_list_class)
    print("e2_list_class", e2_list_class)
    print("e1_list_property", e1_list_property)
    print("e2_list_property", e2_list_property)

    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


def common_member(a, b):
    result = [i for i in a if i in b]
    return result


def calculate_metrics(true_path, predict_path):
    df_true = pd.read_csv(true_path, encoding="Windows-1250")
    df_predict = pd.read_csv(predict_path, encoding="Windows-1250")
    if df_predict.empty:
        return [0, 0, 0]
    else:
        list_true = df_true.values.tolist()
        list_predict = df_predict.values.tolist()
        common = common_member(list_true, list_predict)
        # print("common", common)
        ra = len(common)
        # print("ra", ra)
        r = len(df_true)
        # print("r", r)
        a = len(df_predict)
        # print("a", a)

        precision = ra / a
        recall = ra / r
        f1 = 2 * (precision * recall) / (precision + recall)
        return ["%.2f" % (precision * 100), "%.2f" % (recall * 100), "%.2f" % (f1 * 100)]


if __name__ == '__main__':

    # file path
    o1_path = "../data/conference/cmt-conference/component/source.xml"
    o2_path = "../data/conference/cmt-conference/component/target.xml"
    align_path = "../data/conference/cmt-conference/component/reference.xml"
    predict_path = "rag/predict_target.csv"
    true_path = "rag/true.csv"

    # find true value
    find_alignment(align_path, o1_path, o2_path, true_path)
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities(o1_path, o2_path)

    # load openai API
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

    # load external knowledge
    recurSplitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20, length_function=len)
    with open('rag/initial_verbalise.txt') as init:
        txt_init = init.read()
    initial_docs = recurSplitter.create_documents([txt_init])
    vectorstore_initial = FAISS.from_documents(initial_docs, embedding=OpenAIEmbeddings())
    retriever_initial = vectorstore_initial.as_retriever()
    tool_initial = create_retriever_tool(
        retriever_initial,
        "search_initial_information",
        "Useful for when you need to answer questions about initial matching."
    )
    with open('rag/lexical_verbalise.txt') as lexical:
        txt_lexical = lexical.read()
    lexical_docs = recurSplitter.create_documents([txt_lexical])
    vectorstore_lexical = FAISS.from_documents(lexical_docs, embedding=OpenAIEmbeddings())
    retriever_lexical = vectorstore_lexical.as_retriever()
    tool_lexical = create_retriever_tool(
        retriever_lexical,
        "search_lexical_information",
        "Useful for when you need to answer questions about lexical matching."
    )
    with open('rag/graphical_verbalise.txt') as graph:
        txt_graph = graph.read()
    graphical_docs = recurSplitter.create_documents([txt_graph])
    vectorstore_graphical = FAISS.from_documents(graphical_docs, embedding=OpenAIEmbeddings())
    retriever_graphical = vectorstore_graphical.as_retriever()
    tool_graphical = create_retriever_tool(
        retriever_graphical,
        "search_graphical_information",
        "Useful for when you need to answer questions about graphical matching."
    )

    # combine two documents
    # documents = initial_docs + lexical_docs + graphical_docs

    # define agent
    tools = [tool_initial, tool_lexical, tool_graphical]
    llm = ChatOpenAI(temperature=0)
    agent_executor = create_conversational_retrieval_agent(llm, tools, verbose=True)

    # result = agent_executor({"input": "Is cmt:Co-author equivalent to conference:Contribution_co-author? "
    #                                     "Think step by step. "
    #                                     "Use initial matching, lexical matching, and graphical matching in a sequential order and refine the answer. "
    #                                     "Please answer True if yes, False if not or unknown."})
    # print(result['output'])

    # generate predict
    util.create_document(predict_path, header=['Entity1', 'Entity2'])
    with open(predict_path, "a+", newline='') as f1:
        for e1 in e1_list_class:
            for e2 in e2_list_class:
                # result = agent_executor({"input": "What is equivalent to cmt:Chairman in the conference ontology? Think step by step."})
                result = agent_executor({"input": "Is " + e1 + "equivalent to " + e2 + "? "
                                        "Take a deep breath and work on this problem step-by-step. " # Google OPRO instead of Let's think step by step.
                                        "Consider initial matching, lexical matching, and graphical matching. "
                                        "Please answer True if yes, False if not or unknown."})
                output = result['output']
                # print(output)
                if "True" in output or "true" in output:
                    writer = csv.writer(f1)
                    list_pair = [e1, e2]
                    writer.writerow(list_pair)
        for e1 in e1_list_property:
            for e2 in e2_list_property:
                # result = agent_executor({"input": "What is equivalent to cmt:Chairman in the conference ontology? Think step by step."})
                result = agent_executor({"input": "Is " + e1 + "equivalent to " + e2 + "? "
                                        "Think step by step. "
                                        "Use initial matching, lexical matching, and graphical matching in a sequential order and refine the answer. "
                                        "Please answer True if yes, False if not or unknown."})
                output = result['output']
                # print(output)
                if "True" in output or "true" in output:
                    writer = csv.writer(f1)
                    list_pair = [e1, e2]
                    writer.writerow(list_pair)

    # compare predict and true
    print(calculate_metrics(true_path, predict_path))


    # You are an agent designed to answer questions.
    # You have access to tools for interacting with different sources, and the inputs to the tools are questions.
    # Your main task is to decide which of the tools is relevant for answering question at hand.
    # For complex questions, you can break the question down into sub questions and use tools to answers the sub questions.

    # Vectorstore
    # vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")
    #
    # # LLM
    # llm = ChatOpenAI(temperature=0)
    #
    # # Search
    # search = GoogleSearchAPIWrapper()
    # web_research_retriever = WebResearchRetriever.from_llm(
    #     vectorstore=vectorstore,
    #     llm=llm,
    #     search=search,
    # )
    #
    # tool_google = create_retriever_tool(
    #     web_research_retriever,
    #     "search_ontology_text_information",
    #     "Useful for when you need to answer questions about the meaning of words."
    # )
