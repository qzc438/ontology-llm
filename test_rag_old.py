import util
import os
import dotenv
import pandas as pd
import rdflib
import csv
import json
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

recurSplitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20, length_function=len)

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


def compare_entities(list_source, list_target):
    # compare entities
    for e1 in list_source:
        for e2 in list_target:
            content = chain.invoke(
                "Think step by step."
                "result: Is " + e1 + "equivalent to " + e2 + "? Answer True if yes, False if not or unknown."
                "confidence: give a confidence score between 0 and 1 based on similarity."
                "Format the output as JSON with the following keys: result, confidence."
            )
            print(e1, e2, content)
            # https://towardsdatascience.com/use-langchains-output-parser-with-chatgpt-for-structured-outputs-cf536f692685
            try:
                json_object = json.loads(content)
                # save to predict.csv
                threshold = 1
                if json_object["result"] and json_object["confidence"] >= threshold:
                    with open(predict_path, "a+", newline='') as f1:
                        writer = csv.writer(f1)
                        list_pair = [e1, e2]
                        writer.writerow(list_pair)
            except:
                print("wrong content", content)


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
    o1_path = "cmt-conference/component/source.xml"
    o2_path = "cmt-conference/component/target.xml"
    align_path = "cmt-conference/component/reference.xml"
    predict_path = "predict.csv"
    true_path = "true.csv"

    # find true value
    find_alignment(align_path, o1_path, o2_path, true_path)
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities(o1_path, o2_path)

    # load openai API
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    # load external knowledge
    with open('initial_verbalise.txt') as init:
        txt_init = init.read()
    initial_docs = recurSplitter.create_documents([txt_init])
    with open('graphical_verbalise.txt') as graph:
        txt_graph = graph.read()
    graphical_docs = recurSplitter.create_documents([txt_graph])
    # combine two documents
    documents = initial_docs + graphical_docs
    # save to vector database
    vectorstore = FAISS.from_documents(documents, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    # define model parameters
    template = """Answer the question based only on the following context:
       {context}
       Question: {question}
       """
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI(temperature=0)
    chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
    )

    # find predict value
    util.create_document(predict_path, header=['Entity1', 'Entity2'])
    compare_entities(e1_list_class, e2_list_class)
    compare_entities(e1_list_property, e2_list_property)
    # compare true and predict value
    print(calculate_metrics(true_path, predict_path))

    # print(chain.invoke(
    #                    # "Given the source ontology property assign external reviewer. "
    #                    " Given mark conflict of interest in the source ontology, what is the most similar property in the target ontology?"
    #                    "Think step by step. "
    #                    # "Only answer the class name. "
    #                    # "Please also give a confidence score between 0 and 1 based on similarity."
    #                    ))

    # print(chain.invoke(
    #                    "Given the source ontology property assign external reviewer. "
    #                    " Please compare the similarity of subject area in the source ontology and topic in the target ontology. "
    #                    "Think step by step. "
    # "Only answer the class name. "
    # "Please also give a confidence score between 0 and 1 based on similarity."
    # ))

    # print(chain.invoke(
    #     "Is paper equivalent to paper? "
    #     "Think step by step. "
    #     "Answer only yes or no. "
    #     "Please also give a confidence score between 0 and 1 based on similarity."
    # ))

    # class TwitterUser(BaseModel):
    #     result: str = Field(description="Result, yes or no.")
    #     confidence: str = Field(description="confidence score.")
    #
    #
    # parser = PydanticOutputParser(pydantic_object=TwitterUser)

    # content = (chain.invoke(
    #     "Is " + e1 + "equivalent to " + e2 + "? "
    #     "Think step by step. "
    #     "Answer only yes or no. "
    #     "Please also give a confidence score between 0 and 1 based on similarity."
    # ))
    # print("content", content)
    # print("parsed", parser.parse (content)
