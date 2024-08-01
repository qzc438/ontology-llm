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


# start entity retrieval tools
def get_entity_label(entity, ontology):
    entity_label = ""
    results_rdfs = set(ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.label, None)))
    results_skos = set(ontology.triples((rdflib.URIRef(entity), rdflib.SKOS.prefLabel, None)))
    combined_results = results_rdfs.union(results_skos)
    for s, p, o in combined_results:
        entity_label = str(o)
    return entity_label


def get_entity_name(entity, ontology, ontology_is_code):
    if ontology_is_code:
        entity_name = get_entity_label(entity, ontology) or util.uri_to_name(entity)
    else:
        entity_name = util.uri_to_name(entity)
    return entity_name


@tool
def syntactic(entity: str) -> str:
    """Retrieve syntactic information."""
    util.print_colored_text(f"Retrieve syntactic information: {entity}", "green")
    # entity_name = entity
    # find entity name
    entity_name = get_entity_name(entity, ontology, ontology_is_code)
    cleaned_entity_name = util.cleaning(entity_name)
    print("syntactic_information:", cleaned_entity_name)
    return cleaned_entity_name


@tool
def lexical(entity: str) -> str:
    """Retrieve lexical information."""
    util.print_colored_text(f"Retrieve lexical information: {entity}", "yellow")
    # entity_name = entity
    # find entity name
    entity_name = get_entity_name(entity, ontology, ontology_is_code)
    # extract extra information
    extra_information_set = set()
    for s, p, o in ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.comment, None)):
        extra_information_set.add(str(o))
    for s, p, o in ontology.triples((rdflib.URIRef(entity), rdflib.SKOS.definition, None)):
        extra_information_set.add(str(o))
    extra_information = ' '.join(extra_information_set)
    # create different prompts based on extra information
    if extra_information:
        print("extra_lexical_information:", extra_information)
        prompt = PromptTemplate(
            input_variables=["entity_name", "entity_info", "context"],
            template="Question: What is the meaning of {entity_name}?\n"
                     "Context: {context}\n"
                     "Extra Information: {extra_information}\n"
                     "Answer the question within the context and using the extra information.\n"
        )
        chain = prompt | llm
        response = chain.invoke({
            'entity_name': entity_name,
            'context': context,
            'extra_information': extra_information,
        })
    else:
        prompt = PromptTemplate(
            input_variables=["entity_name", "entity_info", "context"],
            template="Question: What is the meaning of {entity_name}?\n"
                     "Context: {context}\n"
                     "Answer the question within the context.\n"
        )
        chain = prompt | llm
        response = chain.invoke({
            'entity_name': entity_name,
            'context': context,
        })
    # print
    answer = response.content
    print("lexical_information:", answer)
    return answer


@tool
def semantic(entity: str) -> str:
    """Retrieve semantic information."""
    util.print_colored_text(f"Retrieve semantic information: {entity}", "magenta")
    # # find entity uri
    # global entity_uri
    # entity = entity_uri
    # create a subgraph to store entity's semantic information
    subgraph = rdflib.Graph()
    # write the triples to the txt
    relevant_list = [rdflib.RDFS.subClassOf, rdflib.OWL.disjointWith, rdflib.RDFS.domain, rdflib.RDFS.range]
    for predicate in relevant_list:
        for s, p, o in ontology.triples((rdflib.URIRef(entity), predicate, None)):
            if o != rdflib.OWL.Thing and not isinstance(o, rdflib.BNode):
                sub = rdflib.Literal(get_entity_name(s, ontology, ontology_is_code))
                # pre = rdflib.Literal(get_entity_name(p, ontology, ontology_is_code))
                obj = rdflib.Literal(get_entity_name(o, ontology, ontology_is_code))
                subgraph.add((sub, p, obj))
        for s, p, o in ontology.triples((None, predicate, rdflib.URIRef(entity))):
            if s != rdflib.OWL.Thing:
                sub = rdflib.Literal(get_entity_name(s, ontology, ontology_is_code))
                # pre = rdflib.Literal(get_entity_name(p, ontology, ontology_is_code))
                obj = rdflib.Literal(get_entity_name(o, ontology, ontology_is_code))
                subgraph.add((sub, p, obj))
    # save the subgraph
    subgraph.serialize(format="turtle", destination="subgraph.ttl")
    # verbalise the subgraph
    if subgraph:
        # serialize the subgraph once for both saving and using in the prompt
        serialized_subgraph = subgraph.serialize(format="turtle")
        prompt = PromptTemplate(
            input_variables=["subgraph"],
            template="Verbalise triples into phrases: {subgraph}"
        )
        chain = prompt | llm
        response = chain.invoke({'subgraph': serialized_subgraph})
        answer = response.content
    else:
        answer = null_value_sentence
    # print
    print("semantic_information:", answer)
    return answer


# start ontology retrieval tools
def find_all_entities():
    # here entity is uri
    e1_list_class = []
    e2_list_class = []
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x and ("#" in x or "/" in x) and x != rdflib.OWL.Thing:
            e1_list_class.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y and ("#" in y or "/" in y) and y != rdflib.OWL.Thing:
            e2_list_class.append(y)
    e1_list_property = []
    e2_list_property = []
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
    print()
    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


def find_entity_information(path, entity_list, source_or_target, entity_type):
    # entity_list = ["http://cmt#User"] # test keyword
    with open(path, "a+", newline='') as f1:
        for entity in entity_list:
            # small models sometimes have issues passing the URI argument
            # error message: json.decoder.JSONDecodeError: Invalid \escape
            # fix by this solution by passing the entity name to the model
            # but you still need an uri for semantic information
            # global entity_uri
            # entity_uri = entity
            # print("entity_uri:", entity)
            # entity = get_entity_name(entity, ontology, ontology_is_code)
            # print("entity_name:", entity)
            # find information
            print("entity:", entity)
            chain = create_tool_use_agent(retrieval_tools, retrieval_tool_chain)
            # syntactic information
            syntactic_prompt = f"Retrieve syntactic information about {entity}"
            syntactic_information = chain.invoke({"input": syntactic_prompt})
            # lexical information
            lexical_prompt = f"Retrieve lexical information about {entity}"
            lexical_information = chain.invoke({"input": lexical_prompt})
            # semantic information
            semantic_prompt = f"Retrieve semantic information about {entity}"
            semantic_information = chain.invoke({"input": semantic_prompt})
            print()
            # save information
            writer = csv.writer(f1)
            list_information = [entity, source_or_target, entity_type, syntactic_information, lexical_information, semantic_information]
            writer.writerow(list_information)

            # # only work for llm support tool calling
            # chain = always_call_tool_llm | call_tools
            # # find syntactic information
            # syntactic_query = f"Find syntactic information about {entity}"
            # syntactic_result = chain.invoke(syntactic_query)
            # syntactic_information = syntactic_result[0].get("output")
            # # find lexical information
            # lexical_query = f"Find lexical information about {entity}"
            # lexical_result = chain.invoke(lexical_query)
            # lexical_information = lexical_result[0].get("output")
            # # find semantic information
            # semantic_query = f"Find semantic information about {entity}"
            # semantic_result = chain.invoke(semantic_query)
            # semantic_information = semantic_result[0].get("output")


@tool
def init():
    """Ontology retrieval."""
    util.print_colored_text("Ontology Retrieval:", "blue")
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    # create csv
    header = ['entity', 'source_or_target', 'entity_type', 'syntactic_matching', 'lexical_matching', 'semantic_matching']
    util.create_document(csv_path, header=header)
    # re-define global variables
    global ontology, ontology_prefix, ontology_is_code
    # find source ontology information
    ontology, ontology_is_code = o1, o1_is_code
    find_entity_information(csv_path, e1_list_class, "Source", "Class")
    find_entity_information(csv_path, e1_list_property, "Source", "Property")
    # find target ontology information
    ontology, ontology_is_code = o2, o2_is_code
    find_entity_information(csv_path, e2_list_class, "Target", "Class")
    find_entity_information(csv_path, e2_list_property, "Target", "Property")
    return "Retrieve ontology information successfully."


retrieval_tools = [syntactic, lexical, semantic, init]


def retrieval_tool_chain(model_output):
    tool_map = {tool.name: tool for tool in retrieval_tools}
    chosen_tool = tool_map[model_output["name"]]
    return itemgetter("arguments") | chosen_tool


# # The follow code only work for llm support tool calling
# always_call_tool_llm = llm.bind_tools(tools, tool_choice="any")
# tool_map = {tool.name: tool for tool in tools}
#
#
# def call_tools(msg: AIMessage) -> Runnable:
#     """Simple sequential tool calling helper."""
#     tool_map = {tool.name: tool for tool in tools}
#     tool_calls = msg.tool_calls.copy()
#     for tool_call in tool_calls:
#         tool_call["output"] = tool_map[tool_call["name"]].invoke(tool_call["args"])
#     return tool_calls
#
#
# # can be replaced with any prompt that includes variables "agent_scratchpad" and "input"
# # prompt = hub.pull("hwchase17/openai-tools-agent")
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are a helpful assistant. Make sure to only use tools provided to retrieve the information.",
#         ),
#         ("placeholder", "{chat_history}"),
#         ("human", "{input}"),
#         ("placeholder", "{agent_scratchpad}"),
#     ]
# )
# prompt.pretty_print()
# # construct the tool calling agent
# agent = create_tool_calling_agent(llm, tools, prompt)
# # create an agent executor by passing in the agent and tools
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def create_tool_use_agent(tools, tool_chain):
    # try:
    #     prompt = ChatPromptTemplate.from_messages(
    #         [
    #             (
    #                 "system",
    #                 "You are a helpful assistant. Make sure to only use tools provided.",
    #             ),
    #             ("placeholder", "{chat_history}"),
    #             ("human", "{input}"),
    #             ("placeholder", "{agent_scratchpad}"),
    #         ]
    #     )
    #     # construct the tool calling agent
    #     agent = create_tool_calling_agent(llm, tools, prompt)
    #     # create an agent executor by passing in the agent and tools
    #     agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    #     return agent_executor
    # except:
    # define combined prompt
    rendered_tools = render_text_description(tools)
    system_prompt = f"""You are an assistant who has access to the following set of tools.
                    Here are the names and descriptions of each tool:
                    {rendered_tools}
                    Given the user input, return the name of the tool to use and the arguments passed to the tool.
                    Return your response as a JSON blob with the key 'name' and 'arguments'.
                    The value associated with the key 'arguments' should be a dictionary of parameters.
                    """
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{input}")]
    )
    # define chain
    chain = prompt | llm | JsonOutputParser() | tool_chain
    return chain


if __name__ == '__main__':
    # can only calculate OpenAI models
    with get_openai_callback() as cb:
        # find true value
        find_reference(align_path, true_path)
        # run retrieval agent - Part 1
        chain = create_tool_use_agent(retrieval_tools, retrieval_tool_chain)
        response = chain.invoke({"input": "Ontology retrieval."})
        print("response:", response)
        # calculate cost
        print(f"total tokens: {cb.total_tokens}")
        print(f"prompt tokens: {cb.prompt_tokens}")
        print(f"completion tokens: {cb.completion_tokens}")
        print(f"total cost (USD): ${cb.total_cost}")
        # save cost
        print(util.calculate_cost(cb.total_tokens, cb.total_cost, cost_path, util.find_model_name(llm), alignment + "llm_with_retrieve_agent_1"))

    # # agent only support API-accessed models
    # agent_executor.invoke({"input": "Find ontology information."})
    # # multilinguistic, Chinese/French
    # chain.invoke({"input": f"获取本体信息."})
    # chain.invoke({"input": f"Récupérer des informations sur l'ontologie."})
