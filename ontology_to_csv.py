import util
import os
import dotenv
import rdflib
import csv
import torch
import pandas as pd

from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

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


def define_llm():
    llm = ChatOpenAI(temperature=0)
    return llm


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


def split_input(input_string: str):
    return input_string.split(",")


def initial_matching(entity):
    return util.cleaning(util.prefix_name_to_name(entity))


def lexical_matching(entity, prefix):
    entity_full_uri = util.prefix_name_to_uri(entity, prefix)
    entity_label = ""
    for s, p, o in o1.triples((entity_full_uri, rdflib.RDFS.comment, None)):
        entity_label = str(o)
    # print("entity_label:", entity_label)
    entity_lexical = retrieve_complete_lexical_information(entity, entity_label)
    # print("entity_lexical:", entity_lexical)
    return entity_lexical


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
            'entity': util.prefix_name_to_name(entity)
        }).strip()
    else:
        lexical_information = chain.run({
            'background': "",
            'entity': util.prefix_name_to_name(entity)
        }).strip()
    return lexical_information


def graphical_matching(entity, ontology, prefix):
    entity_full_uri = util.prefix_name_to_uri(entity, prefix)
    with open('graphical_entity.txt', 'w') as f:
        for s, p, o in ontology.triples((entity_full_uri, None, None)):
            if "#" in s and "#" in p and "#" in o:
                sub = util.uri_to_prefix_name(s, o1)
                pre = util.uri_to_prefix_name(p, o1)
                obj = util.uri_to_prefix_name(o, o1)
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')
    return verbalise_sentence('graphical_entity.txt')


def verbalise_sentence(input_file_path):
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="cmt: is the prefix of the cmt ontology. "
                 "conference: is the prefix of the conference ontology. "
                 "Please verbalise the statement {sentence}."
                 "Think step by step. Tell me the verbalised sentence only."
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    output = ""
    with open(input_file_path, "r") as input_file:
        for line in input_file:
            processed_line = chain.run(line)
            output += processed_line + ' '
    return output


def save_information_to_csv(path, entity_list, source_or_target, entity_type, ontology, prefix):
    with open(path, "a+", newline='') as f1:
        for entity in entity_list:
            writer = csv.writer(f1)
            list_information = [entity, source_or_target, entity_type, initial_matching(entity), lexical_matching(entity, prefix), graphical_matching(entity, ontology, prefix)]
            writer.writerow(list_information)


if __name__ == '__main__':
    # check GPU
    print("GPU:", torch.cuda.is_available())
    # define llm
    llm = define_llm()
    # define tools
    tools = define_tools()
    # define agents
    agent = define_agents(llm, tools)

    # find true value
    find_alignment(align_path, true_path)
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    # find predict value
    csv_path = "ontology_matching.csv"
    header = ['entity', 'source_or_target', 'entity_type', 'initial_matching', 'lexical_matching', 'graphical_matching']
    util.create_document(csv_path, header=header)
    save_information_to_csv(csv_path, e1_list_class, "Source", "Class", o1, o1_prefix)
    save_information_to_csv(csv_path, e2_list_class, "Target", "Class", o2, o2_prefix)
    save_information_to_csv(csv_path, e1_list_property, "Source", "Property", o1, o1_prefix)
    save_information_to_csv(csv_path, e2_list_property, "Target", "Property", o2, o2_prefix)

    # compare predict and true
    # print(calculate_metrics(true_path, predict_path))
