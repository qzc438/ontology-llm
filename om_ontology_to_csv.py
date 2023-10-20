import util
import os
import dotenv
import rdflib
import csv
import json
import torch

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# customer settings

o1_path = "cmt-conference/component/source.xml"
o2_path = "cmt-conference/component/target.xml"
align_path = "cmt-conference/component/reference.xml"
context = "conference"

# o1_path = "anatomy/mouse-human-suite/component/source.xml"
# o2_path = "anatomy/mouse-human-suite/component/target.xml"
# align_path = "anatomy/mouse-human-suite/component/reference.xml"
# context = "anatomy"

# load api
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# general settings
predict_path = "rag/predict.csv"
true_path = "rag/true.csv"
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"


def define_llm():
    llm = ChatOpenAI(temperature=0)
    return llm


def find_alignment(align_path, true_path):
    # here entity is prefix name
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # create true csv
    util.create_document(true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            e1 = util.uri_to_prefix_name(align.value(s, alignEntity1, None), o1_prefix)
            e2 = util.uri_to_prefix_name(align.value(s, alignEntity2, None), o2_prefix)
            list_pair = [e1, e2]
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


def initial_matching(entity):
    # here entity is name only
    return util.cleaning(util.uri_to_name(entity))


def lexical_matching(entity, ontology):
    entity_label = ""
    for s, p, o in ontology.triples((entity, rdflib.RDFS.comment, None)):
        entity_label = entity_label + str(o)
    for s, p, o in ontology.triples((entity, rdflib.RDFS.label, None)):
        entity_label = entity_label + str(o)
    print("entity_label:", entity_label)
    entity_lexical = retrieve_complete_lexical_information(entity, entity_label)
    print("entity_lexical:", entity_lexical)
    return entity_lexical


def retrieve_complete_lexical_information(entity, entity_label):
    # here entity is name only
    entity_name = util.uri_to_name(entity)
    llm = define_llm()
    if entity_label:
        prompt = PromptTemplate(
            input_variables=["entity", "context", "background"],
            template="{entity} refers to {background}. Determine whether {entity} is a unique identifier or code."
                     "If {entity} is not a unique identifier or code, in the context of {context}, what is the meaning of {entity}? "
                     "If {entity} is a unique identifier or code, in the context of {context}, what is the meaning of {background}?",
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        lexical_information = chain.run({
            'entity': entity_name,
            'background': entity_label,
            'context': context,
        }).strip()
    else:
        prompt = PromptTemplate(
            input_variables=["entity", "context"],
            template="In the context of {context}, what is the meaning of {entity}? "
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        lexical_information = chain.run({
            'entity': entity_name,
            'background': entity_label,
            'context': context,
        }).strip()

    return lexical_information


def graphical_matching(entity, ontology):
    # here entity is name only
    with open('graphical_entity.txt', 'w') as f:
        for s, p, o in ontology.triples((entity, None, None)):
            if "#" in s and "#" in p and "#" in o:
                if str(p).split("#")[-1] != "type":
                    sub = util.uri_to_name(s)
                    pre = util.uri_to_name(p)
                    obj = util.uri_to_name(o)
                    f.write("%s %s %s." % (sub, pre, obj))
                    f.write('\n')
    return verbalise_sentence('graphical_entity.txt')


def verbalise_sentence(input_file_path):
    llm = define_llm()
    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="Please verbalise the following sentence: {sentence}."
                 "answer: the verbalised sentence."
                 "Format the output as JSON with the following keys: answer."
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    output = ""
    with open(input_file_path, "r") as input_file:
        for line in input_file:
            processed_line = chain.run(line)
            processed_line_json = json.loads(processed_line)
            answer = processed_line_json['answer']
            output += answer + ' '
    return output


def save_information_to_csv(path, entity_list, source_or_target, entity_type, ontology, prefix):
    with open(path, "a+", newline='') as f1:
        for entity in entity_list:
            writer = csv.writer(f1)
            list_information = [util.uri_to_prefix_name(entity, prefix), source_or_target, entity_type,
                                initial_matching(entity), lexical_matching(entity, ontology),
                                graphical_matching(entity, ontology)]
            writer.writerow(list_information)


if __name__ == '__main__':
    # check GPU
    print("GPU:", torch.cuda.is_available())
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
