import csv
from operator import itemgetter

import rdflib

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool, render_text_description

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain import hub
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnablePassthrough

from langchain_community.callbacks import get_openai_callback

import run_config as config
import util


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
alignRelation = config.alignRelation

# load ontology
o1 = config.o1
o2 = config.o2

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
entity_uri = None

# calculate cost
cost_path = config.cost_path
alignment = config.alignment


def find_reference(align_path, true_path):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # create true csv
    util.create_document(true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            relation = align.value(s, alignRelation, None)
            if str(relation) == "=":
                e1_uri = align.value(s, alignEntity1, None)
                e2_uri = align.value(s, alignEntity2, None)
                # e1_name = get_entity_name(e1_uri, o1, o1_is_code)
                # e2_name = get_entity_name(e2_uri, o2, o2_is_code)
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

if __name__ == '__main__':
    find_reference(align_path, true_path)