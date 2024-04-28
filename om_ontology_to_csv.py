import run_config as config
import util

import re
import rdflib
import csv
import json

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.tools import Tool

from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate

# customer settings
o1_path = config.o1_path
o2_path = config.o2_path
align_path = config.align_path
context = config.context
o1_is_code = config.o1_is_code
o2_is_code = config.o2_is_code

# load true
true_path = config.true_path
alignCell = config.alignCell
alignEntity1 = config.alignEntity1
alignEntity2 = config.alignEntity2

# load ontology
o1 = config.o1
o2 = config.o2
o1_prefix = config.o1_prefix
o2_prefix = config.o2_prefix

# load llm
llm = config.llm

# null value
null_value_sentence = config.null_value_sentence

# intermediate csv file
csv_path = config.csv_path

# intermediate variables
ontology = None
ontology_is_code = None
ontology_prefix = None


def define_tools():
    tools = [
        Tool(
            name="syntactic_retrieving",
            func=syntactic_retrieving,
            description="Useful for when you need syntactic retrieving."
        ),
        Tool(
            name="lexical_retrieving",
            func=lexical_retrieving,
            description="Useful for when you need lexical retrieving."
        ),
        Tool(
            name="graphical_retrieving",
            func=graphical_retrieving,
            description="Useful for when you need graphical retrieving."
        ),
    ]
    return tools


# you can also use llm to check is code or not
# def check_name_or_code(entity):
#     prompt = PromptTemplate(
#         input_variables=["entity"],
#         template="Is {entity} a unique identifier or code? Please answer True if yes, False if not or unknown."
#     )
#     llm = config.llm
#     chain = LLMChain(llm=llm, prompt=prompt)
#     output = chain.invoke({'entity': entity, })['text']
#     return output


def define_agent(llm, tools):
    agent = create_conversational_retrieval_agent(llm, tools, verbose=True)
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
            e1_uri = align.value(s, alignEntity1, None)
            e2_uri = align.value(s, alignEntity2, None)
            # e1_name = get_entity_name(e1_uri, o1, o1_is_code)
            # e2_name = get_entity_name(e2_uri, o2, o2_is_code)
            # e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
            # e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
            list_pair = [e1_uri, e2_uri]
            writer.writerow(list_pair)
    # read old csv
    with open(true_path, "r") as f:
        reader = csv.reader(f)
        data = list(reader)
    # sort data
    sorted_data = sorted(data, key=lambda x: x[0])
    # write new csv
    with open(true_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sorted_data)


def find_all_entities():
    # here entity is uri
    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x and ("#" in x or "/" in x):
            e1_list_class.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y and ("#" in y or "/" in y):
            e2_list_class.append(y)
    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x and ("#" in x or "/" in x):
            e1_list_property.append(x)
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x and ("#" in x or "/" in x):
            e1_list_property.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y and ("#" in y or "/" in y):
            e2_list_property.append(y)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y and ("#" in y or "/" in y):
            e2_list_property.append(y)
    # sort each list
    e1_list_class.sort()
    e2_list_class.sort()
    e1_list_property.sort()
    e2_list_property.sort()
    # check each list
    print("e1_list_class:", len(e1_list_class))
    print("e2_list_class:", len(e2_list_class))
    print("e1_list_property:", len(e1_list_property))
    print("e2_list_property:", len(e2_list_property))
    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


def get_entity_label(entity, ontology):
    entity_label = ""
    results_rdfs = set(ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.label, None)))
    results_skos = set(ontology.triples((rdflib.URIRef(entity), rdflib.SKOS.prefLabel, None)))
    combined_results = results_rdfs.union(results_skos)
    for s, p, o in combined_results:
        entity_label = str(o)
    # print(entity_label)
    return entity_label


def get_entity_name(entity, ontology, ontology_is_code):
    if ontology_is_code:
        entity_name = get_entity_label(entity, ontology) or util.uri_to_name(entity)
    else:
        entity_name = util.uri_to_name(entity)
    return entity_name


# syntactic_retrieving
def syntactic_retrieving(entity):
    entity_name = get_entity_name(entity, ontology, ontology_is_code)
    prompt = PromptTemplate(
        input_variables=["entity_name"],
        template="Normalise the following name: {entity_name}\n"
                 "Use a lowercase, space-separate format.\n"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    answer = chain.invoke({
        'entity_name': entity_name,
    })
    # print
    print("syntactic_retrieving:", answer['text'])
    return answer['text']


def lexical_retrieving(entity):
    entity_name = get_entity_name(entity, ontology, ontology_is_code)
    # extract extra information
    extra_information_set = set()
    for s, p, o in ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.label, None)):
        extra_information_set.add(str(o))
    for s, p, o in ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.comment, None)):
        extra_information_set.add(str(o))
    for s, p, o in ontology.triples((rdflib.URIRef(entity), rdflib.SKOS.definition, None)):
        extra_information_set.add(str(o))
    extra_information = ' '.join(extra_information_set)
    print("extra_information:", extra_information)
    # create different prompts based on extra information
    if extra_information:
        prompt = PromptTemplate(
            input_variables=["entity_name", "entity_info", "context"],
            template="Question: What is the meaning of {entity_name}?\n"
                     "Context: {context}\n"
                     "Extra Information: {extra_information}\n"
                     "Answer the question within the context and use the extra information."
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        answer = chain.invoke({
            'entity_name': entity_name,
            'context': context,
            'extra_information': extra_information,
        })
    else:
        prompt = PromptTemplate(
            input_variables=["entity_name", "entity_info", "context"],
            template="Question: What is the meaning of {entity_name}?\n"
                     "Context: {context}\n"
                     "Answer the question within the context."
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        answer = chain.invoke({
            'entity_name': entity_name,
            'context': context,
        })
    # print
    print("lexical_retrieving:", answer['text'])
    return answer['text']


def graphical_retrieving(entity):
    # define file name
    file_name = 'graphical_entity.txt'
    # here entity is name only
    with open(file_name, 'w') as f:
        query_subject = list(ontology.triples((rdflib.URIRef(entity), None, None)))
        query_property = list(ontology.triples((None, rdflib.URIRef(entity), None)))
        query_object = list(ontology.triples((None, None, rdflib.URIRef(entity))))
        combined_results = query_subject + query_property + query_object
        for s, p, o in combined_results:
            if "#" in s and "#" in p and "#" in o:
                if str(p).split("#")[-1] != "type" and str(o).split("#")[-1] != "Thing":
                    sub = get_entity_name(s, ontology, ontology_is_code)
                    pre = str(p).split("#")[-1]
                    obj = get_entity_name(o, ontology, ontology_is_code)
                    f.write("%s %s %s." % (sub, pre, obj))
                    f.write('\n')
    # verbalise the triples
    answer = verbalise_sentence(file_name)
    # print
    print("graphical_retrieving:", answer)
    # handle no graphical information
    return answer if answer else null_value_sentence


def verbalise_sentence(input_file_path):
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="Verbalise the following sentence: {sentence}.\n"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    sentence_list = list()
    with open(input_file_path, "r") as input_file:
        for line in input_file:
            processed_line = chain.invoke(line)
            try:
                print("processed_line:", processed_line)
                answer = processed_line['text']
                sentence_list.append(answer)
            except json.JSONDecodeError as e:
                print(f"Cannot verbalise the sentence: {e}")
                sentence_list.append(line)
                continue
    sentences = " ".join(sentence_list)
    return sentences


def save_information_to_csv(path, entity_list, source_or_target, entity_type):
    # entity_list = ["http://cmt#User"] # test keyword
    # entity_list = ["http://cmt#Meta-Reviewer"] # test extra information
    # entity_list = ["http://conference#Organization"] # test null value
    # entity_list = ["http://www.geneontology.org/formats/oboInOwl#DbXref"]  # test null value
    # entity_list = ["http://mouse.owl#MA_0000006`"] # test head/neck
    # entity_list = ["http://mouse.owl#MA_0001844"]
    # entity_list = ["http://human.owl#NCI_C12220"]
    with open(path, "a+", newline='') as f1:
        for entity in entity_list:
            # define template
            syntactic_retrieving = ResponseSchema(name="syntactic_retrieving", description="syntactic retrieving")
            lexical_retrieving = ResponseSchema(name="lexical_retrieving", description="lexical retrieving")
            graphical_retrieving = ResponseSchema(name="graphical_retrieving", description="graphical retrieving")
            response_schema = [syntactic_retrieving, lexical_retrieving, graphical_retrieving]
            output_parser = StructuredOutputParser.from_response_schemas(response_schema)
            format_instructions = output_parser.get_format_instructions()
            # print(format_instructions)
            template = """
                       Find syntactic retrieving about the entity: {entity}
                       Find lexical retrieving about the entity: {entity}
                       Find graphical retrieving about the entity: {entity}
                       {format_instructions}
                       """
            prompt_template = ChatPromptTemplate.from_template(template)
            # combine template with format instructions
            prompt = prompt_template.format_messages(entity=entity, format_instructions=format_instructions)
            print("retrieve prompt:", prompt[0].content)

            # define tools
            tools = define_tools()
            # define agent
            agent = define_agent(llm, tools)
            # execute agent
            result = agent.invoke({"input": prompt})
            output = result['output']
            # print("output:", output)
            # clean comments in json string
            json_no_comments = re.sub(r'//.*', '', output)
            # convert string to dictionary
            output_dict = output_parser.parse(json_no_comments)
            print("output_dict:", output_dict)
            # deal with ```json
            # if output.startswith("```json") and output.endswith("```"):
            #     output = output[7:-3].strip()
            # output_dict = json.loads(output)

            # save information
            syntactic_information = output_dict['syntactic_retrieving']
            lexical_information = output_dict['lexical_retrieving']
            graphical_information = output_dict['graphical_retrieving']
            writer = csv.writer(f1)
            list_information = [entity, source_or_target, entity_type, syntactic_information, lexical_information, graphical_information]
            writer.writerow(list_information)


if __name__ == '__main__':
    # find true value
    find_alignment(align_path, true_path)
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    # create csv
    header = ['entity', 'source_or_target', 'entity_type', 'syntactic_matching', 'lexical_matching', 'graphical_matching']
    util.create_document(csv_path, header=header)
    # find predict value
    ontology, ontology_prefix, ontology_is_code = o1, o1_prefix, o1_is_code
    save_information_to_csv(csv_path, e1_list_class, "Source", "Class")
    save_information_to_csv(csv_path, e1_list_property, "Source", "Property")
    ontology, ontology_prefix, ontology_is_code = o2, o2_prefix, o2_is_code
    save_information_to_csv(csv_path, e2_list_class, "Target", "Class")
    save_information_to_csv(csv_path, e2_list_property, "Target", "Property")