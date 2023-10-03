import os
import dotenv
import rdflib
import util

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import Tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent, create_retriever_tool

# load llm information
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0)

# load ontology information
o1 = rdflib.Graph().parse("cmt-conference/component/source.xml", format="xml")
o2 = rdflib.Graph().parse("cmt-conference/component/target.xml", format="xml")
o1_base_iri = util.find_uri(o1)
o2_base_iri = util.find_uri(o2)
l1 = len(o1_base_iri)
l2 = len(o2_base_iri)

o1_prefix = rdflib.Namespace(o1_base_iri)
o2_prefix = rdflib.Namespace(o2_base_iri)
o1.bind("cmt", o1_prefix)
o2.bind("conference", o2_prefix)


# name to prefix + name
# prefix + name to name
# name to uri  + name


def split_input(input_string: str):
    return input_string.split(",")


def initial_matching(input_string: str):
    e1, e2 = split_input(input_string)

    return util.cleaning(e1.split(":")[-1]) == util.cleaning(e2.split(":")[-1])


def lexical_matching(input_string: str):
    e1, e2 = split_input(input_string)

    e1_full_uri = rdflib.URIRef(o1_prefix[e1.split(":")[-1]])
    e2_full_uri = rdflib.URIRef(o2_prefix[e2.split(":")[-1]])

    e1_label = ""
    e2_label = ""
    for s, p, o in o1.triples((e1_full_uri, rdflib.RDFS.comment, None)):
        e1_label = str(o)
    for s, p, o in o1.triples((e2_full_uri, rdflib.RDFS.comment, None)):
        e2_label = str(o)
    print("e1_label:", e1_label)
    print("e2_label:", e2_label)

    e1_lexical = retrieve_complete_lexical_information(e1, e1_label)
    print("e1_lexical:", e1_lexical)
    e2_lexical = retrieve_complete_lexical_information(e2, e2_label)
    print("e2_lexical:", e2_lexical)
    answer = check_equivalence(e1_lexical, e2_lexical)
    print("answer:", answer)
    if "Yes" in answer or "yes" in answer:
        return True
    else:
        return False


def retrieve_complete_lexical_information(entity: str, label: str):
    prompt = PromptTemplate(
        input_variables=["background", "entity"],
        template="{background}. What is the meaning of {entity} in the context of conference?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    if entity:
        lexical_information = chain.run({
            'background': label,
            'entity': entity.split(":")[-1]
        }).strip()
    else:
        lexical_information = chain.run({
            'background': "",
            'entity': entity.split(":")[-1]
        }).strip()
    return lexical_information


def check_equivalence(e1_sentence: str, e2_sentence: str):
    prompt = PromptTemplate(
        input_variables=["e1_sentence", "e2_sentence"],
        template="Entity 1: {e1_sentence} Entity 2: {e2_sentence} Is Entity 1 equivalent to Entity 2?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    answer = chain.run({
        'e1_sentence': e1_sentence,
        'e2_sentence': e2_sentence
    }).strip()

    return answer


def graphical_matching(input_string: str):
    e1, e2 = split_input(input_string)

    e1_full_uri = rdflib.URIRef(o1_prefix[e1.split(":")[-1]])
    e2_full_uri = rdflib.URIRef(o2_prefix[e2.split(":")[-1]])

    with open('graphical_e1.txt', 'w') as f:
        for s, p, o in o1.triples((e1_full_uri, None, None)):
            if "#" in s and "#" in p and "#" in o:
                sub = o1.namespace_manager.qname(str(s))
                pre = o1.namespace_manager.qname(str(p))
                obj = o1.namespace_manager.qname(str(o))
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')
    verbalise_sentence('graphical_e1.txt', 'graphical_e1_verbalise.txt')
    with open('graphical_e2.txt', 'w') as f:
        for s, p, o in o2.triples((e2_full_uri, None, None)):
            if "#" in s and "#" in p and "#" in o:
                sub = o2.namespace_manager.qname(str(s))
                pre = o2.namespace_manager.qname(str(p))
                obj = o2.namespace_manager.qname(str(o))
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')
    verbalise_sentence('graphical_e2.txt', 'graphical_e2_verbalise.txt')
    answer = check_equivalence_vector_space(e1, e2)
    print("answer:", answer)
    if "Yes" in answer or "yes" in answer:
        return True
    else:
        return False


def verbalise_sentence(input_file_path, output_file_path):
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="cmt: is the prefix of cmt ontology. "
                 "conference: is the prefix of conference ontology. "
                 "Please verbalise the statement {sentence}."
                 "Think step by step. Only answer verbalised sentence."
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    try:
        with open(input_file_path, "r") as input_file, open(output_file_path, "w") as output_file:
            for line in input_file:
                processed_line = chain.run(line)
                output_file.write(processed_line)
                output_file.write('\n')
        print(f"Processed lines written to '{output_file_path}'.")
    except FileNotFoundError:
        print(f"Input file '{input_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def check_equivalence_vector_space(e1: str, e2: str):
    recurSplitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20, length_function=len)
    with open('graphical_e1_verbalise.txt') as f1:
        txt_e1 = f1.read()
    e1_docs = recurSplitter.create_documents([txt_e1])
    with open('graphical_e2_verbalise.txt') as f2:
        txt_e2 = f2.read()
    e2_docs = recurSplitter.create_documents([txt_e2])
    documents = e1_docs + e2_docs
    vectorstore = FAISS.from_documents(documents, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    tool_retriever = create_retriever_tool(
        retriever,
        "graphical-retriever",
        "Useful for when you need to answer questions about graphical retriever."
    )
    tools = [tool_retriever]
    agent_retriever = create_conversational_retrieval_agent(llm, tools, verbose=True)
    answer = agent_retriever({"input": "Is " + e1 + "equivalent to " + e2 + "? "
                            "Take a deep breath and work on this problem step-by-step."})
    return answer


if __name__ == '__main__':
    tools = [
        Tool(
            name="initial-matching",
            func=initial_matching,
            description="useful for when you need initial matching. "
                        "The input to this tool should be a comma separated list of numbers of length two, representing the two entities you want to match together. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
        Tool(
            name="lexical-matching",
            func=lexical_matching,
            description="useful for when you need lexical matching. "
                        "The input to this tool should be a comma separated list of numbers of length two, representing the two entities you want to match together. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
        Tool(
            name="graphical-matching",
            func=graphical_matching,
            description="useful for when you need graphical matching. "
                        "The input to this tool should be a comma separated list of numbers of length two, representing the two entities you want to match together. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
    ]
    agent_executor = create_conversational_retrieval_agent(llm, tools, verbose=True)
    # compare two different terms
    # input_prompt = "Please match cmt:ExternalReviewer and conference:Paper. You can use initial matching, lexical-matching, or graphical matching."
    # compare same terms
    # input_prompt = "Please match cmt:Paper and conference:Paper. You can use initial matching, lexical-matching, or graphical matching."
    # compare two similar terms
    # input_prompt = "Please match cmt:Chairman and conference:Chair. You can use initial matching, lexical-matching, or graphical matching."
    # LLM can determine which tools to use, based on the description
    input_prompt = "Please match cmt:SubjectArea and conference:Topic."
    result = agent_executor({"input": input_prompt})
    output = result['output']
    print(output)
