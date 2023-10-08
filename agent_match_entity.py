import util
import os
import dotenv
import rdflib
import csv
import pandas as pd

import torch
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, initialize_agent, AgentType, LLMSingleActionAgent, AgentExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.agents.agent_toolkits import create_retriever_tool

from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import customer_templete

# check GPU
print("GPU:", torch.cuda.is_available())

# load api
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# load path
o1_path = "cmt-conference/component/source.xml"
o2_path = "cmt-conference/component/target.xml"
align_path = "cmt-conference/component/reference.xml"
predict_path = "rag/predict.csv"
true_path = "rag/true.csv"
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

# load ontology information
o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_base_iri = util.find_uri(o1)
o2_base_iri = util.find_uri(o2)
l1 = len(o1_base_iri)
l2 = len(o2_base_iri)
o1_prefix = rdflib.Namespace(o1_base_iri)
o2_prefix = rdflib.Namespace(o2_base_iri)
o1.bind("cmt", o1_prefix)
o2.bind("conference", o2_prefix)


# read document
# read github
# https://arxiv.org/pdf/2309.03409.pdf


def define_llm():
    llm = ChatOpenAI(temperature=0)
    return llm
    # https://betterprogramming.pub/make-langchain-agent-actually-works-with-local-llms-vicuna-wizardlm-etc-da42b6b1a97
    # llama, graphical matching failed
    # callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    # n_gpu_layers = 40
    # n_batch = 512
    # llm = LlamaCpp(
    #     temperature=0,
    #     n_ctx=2048,
    #     model_path="llama-2-7b-chat.gguf.q4_0.bin",
    #     n_gpu_layers=n_gpu_layers,
    #     n_batch=n_batch,
    #     callback_manager=callback_manager,
    #     verbose=False,  # Verbose is required to pass to the callback manager
    # )

    # # huggingface
    # llm = HuggingFacePipeline.from_model_id(
    #     model_id="bigscience/bloom-1b7",
    #     task="text-generation",
    #     device=0,
    #     model_kwargs={"do_sample": True, "temperature": 0.1, "max_length": 2048},
    # )


def define_tools():
    tools = [
        Tool(
            name="initial-matching",
            func=initial_matching,
            description="useful for when you need initial matching. "
                        "The input to this tool should be a comma-separated list of entities of length two, representing the two entities you want to match. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
        Tool(
            name="lexical-matching",
            func=lexical_matching,
            description="useful for when you need lexical matching. "
                        "The input to this tool should be a comma-separated list of entities of length two, representing the two entities you want to match. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
        Tool(
            name="graphical-matching",
            func=graphical_matching,
            description="useful for when you need graphical matching. "
                        "The input to this tool should be a comma-separated list of entities of length two, representing the two entities you want to match. "
                        "For example, `person,chair` would be the input if you wanted to match person and chair."
        ),
    ]
    return tools


def define_agents(llm, tools):
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True,
                             handle_parsing_errors=True)
    # agent_executor = create_conversational_retrieval_agent(llm, tools, verbose=True)
    return agent


def find_alignment(align_path, true_path):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # create true csv
    util.create_document(true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            e1 = util.uri_to_prefix_name(align.value(s, alignEntity1, None), o1)
            e2 = util.uri_to_prefix_name(align.value(s, alignEntity2, None), o2)
            list_pair = [e1, e2]
            writer.writerow(list_pair)


def find_all_entities():
    # add entities into list
    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x and "#" in x:
            e1_list_class.append(util.uri_to_prefix_name(x, o1))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y and "#" in y:
            e2_list_class.append(util.uri_to_prefix_name(y, o2))
    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x and "#" in x:
            e1_list_property.append(util.uri_to_prefix_name(x, o1))
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x and "#" in x:
            e1_list_property.append(util.uri_to_prefix_name(x, o1))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y and "#" in y:
            e2_list_property.append(util.uri_to_prefix_name(y, o2))
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y and "#" in y:
            e2_list_property.append(util.uri_to_prefix_name(y, o2))

    print("e1_list_class", len(e1_list_class), e1_list_class)
    print("e2_list_class", len(e2_list_class), e2_list_class)
    print("e1_list_property", len(e1_list_property), e1_list_property)
    print("e2_list_property", len(e2_list_property), e2_list_property)

    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


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


def common_member(a, b):
    result = [i for i in a if i in b]
    return result


def split_input(input_string: str):
    return input_string.split(",")


def initial_matching(input_string: str):
    e1, e2 = split_input(input_string)
    return util.cleaning(util.prefix_name_to_name(e1)) == util.cleaning(util.prefix_name_to_name(e2))


def lexical_matching(input_string: str):
    e1, e2 = split_input(input_string)

    e1_full_uri = util.prefix_name_to_uri(e1, o1_prefix)
    e2_full_uri = util.prefix_name_to_uri(e2, o2_prefix)

    e1_label = ""
    e2_label = ""
    for s, p, o in o1.triples((e1_full_uri, rdflib.RDFS.comment, None)):
        e1_label = str(o)
    for s, p, o in o1.triples((e2_full_uri, rdflib.RDFS.comment, None)):
        e2_label = str(o)
    print()
    print("e1_label:", e1_label)
    print("e2_label:", e2_label)

    e1_lexical = retrieve_complete_lexical_information(e1, e1_label)
    print("e1_lexical:", e1_lexical)
    e2_lexical = retrieve_complete_lexical_information(e2, e2_label)
    print("e2_lexical:", e2_lexical)
    answer = check_equivalence(e1_lexical, e2_lexical)
    print("lexical matching: ", answer)
    if "Yes" in answer or "yes" in answer:
        return True
    else:
        return False


def retrieve_complete_lexical_information(entity: str, label: str):
    llm = define_llm()
    prompt = PromptTemplate(
        input_variables=["background", "entity"],
        template="{background}. In the context of a research conference, what is the meaning of {entity}?",
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
    llm = define_llm()
    prompt = PromptTemplate(
        input_variables=["e1_sentence", "e2_sentence"],
        template="Entity 1: {e1_sentence} Entity 2: {e2_sentence} Is Entity 1 the same thing as Entity 2?",
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
                sub = util.uri_to_prefix_name(s, o1)
                pre = util.uri_to_prefix_name(p, o1)
                obj = util.uri_to_prefix_name(o, o1)
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')
    verbalise_sentence('graphical_e1.txt', 'graphical_e1_verbalise.txt')
    with open('graphical_e2.txt', 'w') as f:
        for s, p, o in o2.triples((e2_full_uri, None, None)):
            if "#" in s and "#" in p and "#" in o:
                sub = util.uri_to_prefix_name(s, o2)
                pre = util.uri_to_prefix_name(p, o2)
                obj = util.uri_to_prefix_name(o, o2)
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')
    verbalise_sentence('graphical_e2.txt', 'graphical_e2_verbalise.txt')
    answer = check_equivalence_vector_space(e1, e2)
    # print("graphical matching:", answer)
    if "Yes" in answer or "yes" in answer:
        return True
    else:
        return False


def verbalise_sentence(input_file_path, output_file_path):
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="cmt: is the prefix of the cmt ontology. "
                 "conference: is the prefix of the conference ontology. "
                 "Please verbalise the statement {sentence}."
                 "Think step by step. Tell me the verbalised sentence only."
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
        "Useful for when you need to answer questions about the graphical retriever."
    )
    llm = define_llm()
    tools = [tool_retriever]
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    prompt = "Is {e1} equivalent to {e2}? Take a deep breath and work on this problem step-by-step.".format(e1=e1, e2=e2)
    answer = agent.run(prompt)
    return answer


if __name__ == '__main__':
    # define llm
    llm = define_llm()
    # define tools
    tools = define_tools()
    # define agents
    agent = define_agents(llm,tools)
    # define prompt
    prompt = "Is {e1} equivalent to {e2}?". format(e1="cmt:ExternalReviewer", e2="conference:Paper")
    agent.run(prompt)

    # prompt = customer_templete.CustomPromptTemplate(
    #     template=customer_templete.template,
    #     tools=tools,
    #     # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    #     # This includes the `intermediate_steps` variable because that is needed
    #     input_variables=["input", "intermediate_steps"]
    # )
    #
    # llm_chain = LLMChain(llm=llm, prompt=prompt)
    #
    # tool_names = [tool.name for tool in tools]
    # agent = LLMSingleActionAgent(
    #     llm_chain=llm_chain,
    #     output_parser=customer_templete.output_parser,
    #     stop=["\nObservation:"],
    #     allowed_tools=tool_names
    # )
    # agent = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    # agent.run("Is ExternalReviewer equivalent to Paper? You can use initial matching, lexical-matching, or graphical matching.")

    # # find true value
    # find_alignment(align_path, true_path)
    # # find all entities
    # e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    # # find predict value
    # util.create_document(predict_path, header=['Entity1', 'Entity2'])
    # with open(predict_path, "a+", newline='') as f1:
    #     for e1 in e1_list_class:
    #         for e2 in e2_list_class:
    #             # https://python.langchain.com/docs/modules/agents/how_to/custom_llm_agent
    #             input_prompt = ("Is " + e1 + "match " + e2 + "? "
    #             "You can use initial matching, lexical-matching, or graphical matching. "
    #             "Please answer True if you find at least one match, False if you cannot find any match.")
    #             result = agent.run(input_prompt)
    #             print("Result:", result)
    #             if "True" in result or "true" in result:
    #                 writer = csv.writer(f1)
    #                 list_pair = [e1, e2]
    #                 writer.writerow(list_pair)
    #     for e1 in e1_list_property:
    #         for e2 in e2_list_property:
    #             input_prompt = ("Is " + e1 + "match " + e2 + "? "
    #             "You can use initial matching, lexical-matching, or graphical matching. "
    #             "Please answer True if you find at least one match, False if you cannot find any match.")
    #             result = agent.run(input_prompt)
    #             print("output:", result)
    #             if "True" in result or "true" in result:
    #                 writer = csv.writer(f1)
    #                 list_pair = [e1, e2]
    #                 writer.writerow(list_pair)
    #
    # # compare predict and true
    # print(calculate_metrics(true_path, predict_path))

    # test data
    # compare two different terms
    # input_prompt = "Please match cmt:ExternalReviewer and conference:Paper. You can use initial matching, lexical-matching, or graphical matching."
    # compare same terms
    # input_prompt = "Please match cmt:Paper and conference:Paper. You can use initial matching, lexical-matching, or graphical matching."
    # compare two similar terms
    # input_prompt = "Please match cmt:Chairman and conference:Chair. You can use initial matching, lexical-matching, or graphical matching."
    # LLM can determine which tools to use, based on the description
    # input_prompt = "Please match cmt:SubjectArea and conference:Topic."
