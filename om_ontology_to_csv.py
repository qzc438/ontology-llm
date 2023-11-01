import config
import util

import rdflib
import csv
import json
import torch

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# customer settings
o1_path = config.o1_path
o2_path = config.o2_path
align_path = config.align_path
context = config.context
is_code = config.is_code

# load true
true_path = config.true_path
alignCell = config.alignCell
alignEntity1 = config.alignEntity1
alignEntity2 = config.alignEntity2
# load ontology
o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"
# intermediate csv file
csv_path = config.csv_path


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
            e1_name = get_entity_name(e1_uri, o1)
            e2_name = get_entity_name(e2_uri, o2)
            e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
            e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
            list_pair = [e1_prefix_name, e2_prefix_name]
            writer.writerow(list_pair)


def find_all_entities():
    # here entity is uri
    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x and "#" in x:
            e1_list_class.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y and "#" in y:
            e2_list_class.append(y)
    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x and "#" in x:
            e1_list_property.append(x)
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x and "#" in x:
            e1_list_property.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y and "#" in y:
            e2_list_property.append(y)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y and "#" in y:
            e2_list_property.append(y)

    print("e1_list_class", len(e1_list_class), e1_list_class)
    print("e2_list_class", len(e2_list_class), e2_list_class)
    print("e1_list_property", len(e1_list_property), e1_list_property)
    print("e2_list_property", len(e2_list_property), e2_list_property)

    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


def get_entity_label(entity, ontology):
    entity_label = ""
    for s, p, o in ontology.triples((entity, rdflib.RDFS.label, None)):
        entity_label = str(o)
    return entity_label


def get_entity_name(entity, ontology):
    if is_code:
        entity_name = get_entity_label(entity, ontology) or util.uri_to_name(entity)
    else:
        entity_name = util.uri_to_name(entity)
    return entity_name


def initial_information(entity, ontology):
    entity_name = get_entity_name(entity, ontology)
    llm = config.llm
    prompt = PromptTemplate(
        input_variables=["entity_name"],
        template="Normalise the following entity: {entity_name}. "
                 "Use lowercase and split the words using white space. "
                 "entity_initial: only return the normalised entity. "
                 "Format the output as JSON with the following keys: entity_initial. "
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    answer = chain.run({
        'entity_name': entity_name,
    }).strip()
    entity_initial_json = json.loads(answer)
    entity_initial = entity_initial_json['entity_initial']
    print("entity_initial:", entity_initial)
    return entity_initial


def lexical_information(entity, ontology):
    entity_name = get_entity_name(entity, ontology)
    entity_info = ""
    for s, p, o in ontology.triples((entity, rdflib.RDFS.comment, None)):
        entity_info = entity_info + str(o)
    for s, p, o in ontology.triples((entity, rdflib.RDFS.label, None)):
        entity_info = entity_info + str(o)
    print("entity_info:", entity_info)

    llm = config.llm
    if entity_info:
        prompt = PromptTemplate(
            input_variables=["entity_name", "entity_info", "context"],
            template="{entity_name} is {entity_info}. "
                     "In the context of {context}, what is the meaning of {entity_name}?"
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        answer = chain.run({
            'entity_name': entity_name,
            'entity_info': entity_info,
            'context': context,
        }).strip()
    else:
        prompt = PromptTemplate(
            input_variables=["entity_name", "context"],
            template="In the context of {context}, what is the meaning of {entity_name}? "
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        answer = chain.run({
            'entity_name': entity_name,
            'context': context,
        }).strip()

    print("entity_lexical:", answer)
    return answer


def graphical_information(entity, ontology):
    # here entity is name only
    with open('graphical_entity.txt', 'w') as f:
        query_subject = list(ontology.triples((entity, None, None)))
        query_property = list(ontology.triples((None, entity, None)))
        query_object = list(ontology.triples((None, None, entity)))
        combined_results = query_subject + query_property + query_object
        for s, p, o in combined_results:
            if "#" in s and "#" in p and "#" in o:
                if str(p).split("#")[-1] != "type" and str(o).split("#")[-1] != "Thing":
                    sub = get_entity_name(s, ontology)
                    pre = str(p).split("#")[-1]
                    obj = get_entity_name(o, ontology)
                    f.write("%s %s %s." % (sub, pre, obj))
                    f.write('\n')
    answer = verbalise_sentence('graphical_entity.txt')
    print("entity_graphical:", answer)
    return answer


def verbalise_sentence(input_file_path):
    llm = config.llm
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="Verbalise the following triples: {sentence}. "
                 "entity_graphical: only return the verbalised sentence. "
                 "Format the output as JSON with the following keys: entity_graphical. "
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    output = ""
    with open(input_file_path, "r") as input_file:
        for line in input_file:
            processed_line = chain.run(line)
            processed_line_json = json.loads(processed_line)
            answer = processed_line_json['entity_graphical']
            output += answer + ' '
    return output


def save_information_to_csv(path, entity_list, source_or_target, entity_type, ontology, prefix):
    with open(path, "a+", newline='') as f1:
        for entity in entity_list:
            entity_name = get_entity_name(entity, ontology)
            writer = csv.writer(f1)
            list_information = [util.name_to_prefix_name(entity_name, prefix), source_or_target, entity_type,
                                initial_information(entity, ontology), lexical_information(entity, ontology),
                                graphical_information(entity, ontology)]
            writer.writerow(list_information)


# def check_name_or_code(entity):
#     llm = define_llm()
#     prompt = PromptTemplate(
#         input_variables=["entity"],
#         template="Is {entity} a unique identifier or code?"
#                  "Please answer True if yes, False if not or unknown."
#     )
#     chain = LLMChain(llm=llm, prompt=prompt)
#     output = chain.run({
#         'entity': entity,
#     }).strip()
#     return output


if __name__ == '__main__':
    # check GPU
    print("GPU:", torch.cuda.is_available())
    # find true value
    find_alignment(align_path, true_path)
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    # find predict value
    header = ['entity', 'source_or_target', 'entity_type', 'initial_matching', 'lexical_matching', 'graphical_matching']
    util.create_document(csv_path, header=header)
    save_information_to_csv(csv_path, e1_list_class, "Source", "Class", o1, o1_prefix)
    save_information_to_csv(csv_path, e2_list_class, "Target", "Class", o2, o2_prefix)
    save_information_to_csv(csv_path, e1_list_property, "Source", "Property", o1, o1_prefix)
    save_information_to_csv(csv_path, e2_list_property, "Target", "Property", o2, o2_prefix)