import collections
import csv
import itertools

import sys
import re
import logging
from operator import itemgetter

import pandas as pd

import psycopg2
from pgvector.psycopg2 import register_vector

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool, render_text_description

from langchain_community.callbacks import get_openai_callback

import run_config as config
import om_ontology_to_csv
import generate_anatomy_mse_benchmark as generate
import util


# define path
alignment = config.alignment
result_path = config.result_path

o1_path = config.o1_path
o2_path = config.o2_path
o1_is_code = config.o1_is_code
o2_is_code = config.o2_is_code

align_path = config.align_path
context = config.context

o1 = config.o1
o2 = config.o2

# define search variables
similarity_threshold = config.similarity_threshold
num_matches = config.num_matches
top_k = config.top_k

# define result files
predict_source_path_no_validation = config.predict_source_path_no_validation
predict_target_path_no_validation = config.predict_target_path_no_validation
predict_path_no_validation = config.predict_path_no_validation
predict_source_path = config.predict_source_path
predict_target_path = config.predict_target_path
predict_path = config.predict_path
true_path = config.true_path

# define llm
llm = config.llm

# null value
null_value_matching = config.null_value_matching

# database connection
connection_string = config.connection_string

# define entity metadata
content = ""
source_or_target = ""
entity_type = ""

# create logger
logger = logging.getLogger('agent_log')
# create file handler
fileHandler = logging.FileHandler("agent.log", mode='w')
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

# intermediate values
compare_list = None

# calculate cost
cost_path = config.cost_path

def create_log(message):
    logger = logging.getLogger('agent_log')
    logger.setLevel(logging.INFO)
    logger.info(message)


# start entity matching tools
def find_entity_id(entity, source_or_target):
    conn = psycopg2.connect(connection_string)
    register_vector(conn)
    cursor = conn.cursor()
    sql = '''SELECT o.entity_id FROM ontology_matching o
              WHERE o.entity = (%s) and o.source_or_target = (%s)'''
    cursor.execute(sql, (entity, source_or_target))
    result = cursor.fetchone()
    # print("entity_id:", result[0])
    conn.close()
    return result[0]


def find_entity(entity_id):
    # print("entity_id:", entity_id)
    conn = psycopg2.connect(connection_string)
    register_vector(conn)
    cursor = conn.cursor()
    sql = '''SELECT o.entity FROM ontology_matching o
              WHERE o.entity_id = (%s)'''
    cursor.execute(sql, (entity_id,))
    result = cursor.fetchone()
    # print("entity:", result[0])
    conn.close()
    return result[0]


def entity_matching(entity, table_name):
    # create connection
    conn = psycopg2.connect(connection_string)
    register_vector(conn)
    # find content, source_or_target, entity_type
    cursor = conn.cursor()
    sql = f'''select m.embedding, o.source_or_target, o.entity_type
              from ontology_matching o, {table_name} m
              where o.entity_id = m.entity_id
              and o.entity_id = (%s);'''
    cursor.execute(sql, (entity,))
    result = cursor.fetchone()
    # print("result", result)
    if result:
        # set content value
        content_embedding = result[0].tolist()
        # content = result[0]
        # set source_or_target value
        if result[1] == "Source":
            source_or_target = "Target"
        elif result[1] == "Target":
            source_or_target = "Source"
        # set entity_type value
        if result[2] == "Class":
            entity_type = "Class"
        elif result[2] == "Property":
            entity_type = "Property"
        create_log(f"entity: {entity}, {source_or_target}, {entity_type}, {similarity_threshold}, {num_matches}")

        # find similar entities to the query using cosine similarity search
        # this new feature is provided by `pgvector`
        sql = f'''WITH vector_matches AS (
                      SELECT entity_id, 1 - (embedding <=> '{content_embedding}') AS similarity
                      FROM {table_name}
                      WHERE 1 - (embedding <=> '{content_embedding}') >= %s
                    )
                    SELECT o.entity_id, v.similarity as similarity FROM ontology_matching o, vector_matches v
                    WHERE o.entity_id IN (SELECT entity_id FROM vector_matches)
                    AND o.entity_id =  v.entity_id
                    AND o.source_or_target = (%s) AND o.entity_type = (%s)
                    ORDER BY v.similarity DESC
                    LIMIT %s;
                    '''
        cursor.execute(sql, (similarity_threshold, source_or_target, entity_type, num_matches))
        # define matches for results
        matches = []
        result = cursor.fetchall()
        if len(result) != 0:
            # store results into matches
            for r in result:
                matches.append(
                    {
                        "entity": r[0],
                        table_name: r[1],
                    }
                )
        # close connection
        conn.close()
        create_log(f"matching type: {table_name}, matches: {matches}")
        # print("matches:", matches)
        return matches
    # no result
    return None


@tool
def syntactic(entity: str) -> list:
    """Syntactic matching."""
    util.print_colored_text(f"Syntactic matching: {entity}", "green")
    # tool function
    syntactic_matching = entity_matching(entity, "syntactic_matching")
    syntactic_matches = pd.DataFrame(syntactic_matching)
    syntactic_matches.drop_duplicates(['entity'], inplace=True)
    if len(syntactic_matches) != 0:
        result = syntactic_matches['entity'].head(top_k).values.tolist()
    else:
        result = [null_value_matching]
    print(result)
    return result


@tool
def lexical(entity: str) -> list:
    """Lexical matching."""
    util.print_colored_text(f"Lexical matching: {entity}", "yellow")
    # tool function
    lexical_matching = entity_matching(entity, "lexical_matching")
    lexical_matches = pd.DataFrame(lexical_matching)
    lexical_matches.drop_duplicates(['entity'], inplace=True)
    if len(lexical_matches) != 0:
        result = lexical_matches['entity'].head(top_k).values.tolist()
    else:
        result = [null_value_matching]
    print(result)
    return result


@tool
def semantic(entity: str) -> list:
    """Semantic matching."""
    util.print_colored_text(f"Semantic matching: {entity}", "magenta")
    # tool function
    semantic_matching = entity_matching(entity, "semantic_matching")
    semantic_matches = pd.DataFrame(semantic_matching)
    semantic_matches.drop_duplicates(['entity'], inplace=True)
    if len(semantic_matches) != 0:
        result = semantic_matches['entity'].head(top_k).values.tolist()
    else:
        result = [null_value_matching]
    print(result)
    return result


# start ontology matching tools
def find_all_matching_candidate(entity):
    # define entity matching
    chain = create_tool_use_agent(matching_tools, matching_tool_chain)
    # syntactic_matching
    syntactic_prompt = f"Syntactic matching for {entity}"
    syntactic_matching = chain.invoke({"input": syntactic_prompt})
    # lexical matching
    lexical_prompt = f"Lexical matching for {entity}"
    lexical_matching = chain.invoke({"input": lexical_prompt})
    # semantic matching
    semantic_prompt = f"Semantic matching for {entity}"
    semantic_matching = chain.invoke({"input": semantic_prompt})
    output_dict = {'syntactic_matching': syntactic_matching, 'lexical_matching': lexical_matching, 'semantic_matching': semantic_matching}
    return output_dict


def reciprocal_rank_fusion_all_with_grouped_scores_exclude_none(*rankings):
    reciprocal_ranks = collections.defaultdict(float)
    for ranking in rankings:
        if not isinstance(ranking, (list, tuple)):
            ranking = [ranking]
        for position, item in enumerate(ranking, start=1):
            reciprocal_ranks[item] += 1 / position
    # sort by reciprocal rank value, then by item lexicographically for tie-breaking
    fused_ranking_with_scores = sorted(reciprocal_ranks.items(), key=lambda x: (-x[1], x[0]))
    # group items by their score
    grouped_items_by_score = [(score, [item for item, _ in items]) for score, items in itertools.groupby(fused_ranking_with_scores, key=lambda x: x[1])]
    return grouped_items_by_score


def extract_yes_no(text):
    match = re.search(r'\b(?:yes|no)\b', str(text), flags=re.IGNORECASE)
    return match.group().lower() if match else None


def find_most_relevant_entity(entity, source_or_target):
    # invoke find_all_matching_candidate
    output_json = find_all_matching_candidate(entity)
    # prepare rankings, wrapping string values in lists and filtering out None values
    rankings = [value if isinstance(value, list) else [value] for value in output_json.values() if value != [null_value_matching]]
    print("rankings:", rankings)

    # create list
    candidates_without_validation_and_merge = []
    candidates_with_validation_and_merge = []

    if rankings:
        # call the reciprocal rank fusion function with the processed rankings
        predict_entity_list = reciprocal_rank_fusion_all_with_grouped_scores_exclude_none(*rankings)
        print("entity_id:", entity)
        print("predict_entity_list:", predict_entity_list)
        create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        if predict_entity_list:
            # without validation, select the first one
            scores, predict_entities = predict_entity_list[0]
            for predict_entity in predict_entities:
                candidates_without_validation_and_merge.append(find_entity(predict_entity))

            # with validation
            for scores, predict_entities in predict_entity_list[:top_k]:
                # predict_entities.append("target:TieBreakingTest")
                for predict_entity in predict_entities:
                    # find entity name
                    if source_or_target == "Source":
                        entity_name = om_ontology_to_csv.get_entity_name(find_entity(entity), o1, o1_is_code)
                        predict_entity_name = om_ontology_to_csv.get_entity_name(find_entity(predict_entity), o2, o2_is_code)
                    else:
                        entity_name = om_ontology_to_csv.get_entity_name(find_entity(entity), o2, o2_is_code)
                        predict_entity_name = om_ontology_to_csv.get_entity_name(find_entity(predict_entity), o1, o1_is_code)
                    # clean entity name
                    entity_name_clean = util.cleaning(entity_name)
                    predict_entity_name_clean = util.cleaning(predict_entity_name)
                    # compare entity name
                    if entity_name_clean.casefold() == predict_entity_name_clean.casefold():
                        candidates_with_validation_and_merge.append(find_entity(predict_entity))
                        create_log(f"result_without_validate: {predict_entity_name}")
                        continue
                    # validate matching
                    chain = create_tool_use_agent(matching_tools, matching_tool_chain)
                    global compare_list
                    compare_list = [entity_name_clean, predict_entity_name_clean]
                    # if llm do not allow to pass sensitive word, use this approach
                    validate_prompt = "Validate matching."
                    # validate_prompt = f"""a: {entity_name_clean}
                    #                 b: {predict_entity_name_clean}
                    #                 Validate matching between a and b
                    #                 """
                    validate_result = chain.invoke({"input": validate_prompt})
                    if extract_yes_no(validate_result) == "yes":
                        candidates_with_validation_and_merge.append(find_entity(predict_entity))
                print("candidates_with_validation_and_merge:", candidates_with_validation_and_merge)
                if candidates_with_validation_and_merge:
                    break

    print(f"entity: {entity}, entity matching has been completed.\n")
    create_log(f"entity: {entity}, entity matching has been completed.\n")
    return candidates_without_validation_and_merge, candidates_with_validation_and_merge


# start ontology matching tools
@tool
def init():
    """Ontology matching."""
    util.print_colored_text("Ontology matching:", "blue")
    # tool function

    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
    e1_list = e1_list_class + e1_list_property
    e2_list = e2_list_class + e2_list_property

    # find matching from source ontology
    util.create_document(predict_source_path_no_validation, header=['Entity1', 'Entity2'])
    util.create_document(predict_source_path, header=['Entity1', 'Entity2'])
    # e1_list = ["http://mouse.owl#MA_0001742"] # test sensitive word
    for entity in e1_list:
        print("entity1:", entity)
        entity_id = find_entity_id(entity, "Source")
        candidates_without_validation_and_merge, candidates_with_validation_and_merge = find_most_relevant_entity(entity_id, "Source")
        for candidate in candidates_without_validation_and_merge:
            with open(predict_source_path_no_validation, "a+", newline='') as f:
                writer = csv.writer(f)
                list_pair = [entity, candidate]
                writer.writerow(list_pair)
        for candidate in candidates_with_validation_and_merge:
            with open(predict_source_path, "a+", newline='') as f:
                writer = csv.writer(f)
                list_pair = [entity, candidate]
                writer.writerow(list_pair)
    # clean 8 mappings need to be removed from the anatomy track
    if config.alignment == "anatomy/mouse-human-suite/component/":
        util.filter_anatomy(predict_source_path_no_validation)
        util.filter_anatomy(predict_source_path)
    # evaluation
    print(util.calculate_metrics(true_path, predict_source_path_no_validation, result_path, util.find_model_name(llm), alignment + "source_no_validation"))
    print(util.calculate_metrics(true_path, predict_source_path, result_path, util.find_model_name(llm), alignment + "source"))

    # find matching from target ontology
    util.create_document(predict_target_path_no_validation, header=['Entity2', 'Entity1'])
    util.create_document(predict_target_path, header=['Entity2', 'Entity1'])
    # e2_list = ["http://human.owl#NCI_C25177"] # test sensitive word
    for entity in e2_list:
        print("entity2:", entity)
        entity_id = find_entity_id(entity, "Target")
        candidates_without_validation_and_merge, candidates_with_validation_and_merge = find_most_relevant_entity(entity_id, "Target")
        for candidate in candidates_without_validation_and_merge:
            with open(predict_target_path_no_validation, "a+", newline='') as f:
                writer = csv.writer(f)
                list_pair = [entity, candidate]
                writer.writerow(list_pair)
        for candidate in candidates_with_validation_and_merge:
            with open(predict_target_path, "a+", newline='') as f:
                writer = csv.writer(f)
                list_pair = [entity, candidate]
                writer.writerow(list_pair)
    # clean 8 mappings need to be removed from the anatomy track
    if config.alignment == "anatomy/mouse-human-suite/component/":
        util.filter_anatomy(predict_target_path_no_validation)
        util.filter_anatomy(predict_target_path)
    # evaluation
    print(util.calculate_metrics(true_path, predict_target_path_no_validation, result_path, util.find_model_name(llm), alignment + "target_no_validation"))
    print(util.calculate_metrics(true_path, predict_target_path, result_path, util.find_model_name(llm), alignment + "target"))

    # merge matching
    chain = create_tool_use_agent(matching_tools, matching_tool_chain)
    chain.invoke({"input": "Merge matching."})

    print("Ontology matching successfully completed.")


# start ontology refine tools
@tool
def merge():
    """Merge matching."""
    util.print_colored_text("Merge matching:", "cyan")
    # tool function
    # matching merge without validation
    df_source_no_validation = pd.read_csv(predict_source_path_no_validation)
    df_target_no_validation = pd.read_csv(predict_target_path_no_validation)
    df_merge_no_validation = pd.merge(df_source_no_validation, df_target_no_validation, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge_no_validation = df_merge_no_validation.drop_duplicates()
    df_merge_no_validation.to_csv(predict_path_no_validation, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path_no_validation, result_path, util.find_model_name(llm), alignment + "no_validation"))
    # matching merge with validation
    df_source = pd.read_csv(predict_source_path)
    df_target = pd.read_csv(predict_target_path)
    df_merge = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge = df_merge.drop_duplicates()
    df_merge.to_csv(predict_path, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path, result_path, util.find_model_name(llm), alignment + "llm_with_agent"))
    # find non-trivial alignment in the anatomy track
    if config.alignment == "anatomy/mouse-human-suite/component/":
        generate.generate_filtered_csv("alignment/anatomy/mouse-human-suite/component/predict.csv",
                                       "benchmark_2023/anatomy/trivial.csv",
                                       "benchmark_2023/anatomy/Agent-OM_filter.csv")
        print(util.calculate_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/Agent-OM_filter.csv",
                                     result_path, util.find_model_name(llm),
                                     alignment + "llm_with_agent_filter"))


# if llm do not allow to pass sensitive word, use this approach
@tool
def validate():
    """Validate matching."""
    global compare_list
    a = compare_list[0]
    b = compare_list[1]
    util.print_colored_text(f"Validate matching: {a} and {b}", "cyan")
    # tool function, do not use "" because the name will change to "Head_and_Neck."
    prompt_validate_question = f"""Question: Is {a} equivalent to {b}?
                            Context: {context}
                            Answer the question within the context.
                            Answer yes or no. Give a short explanation.
                            """
    result_validate = llm.invoke(prompt_validate_question)
    print("result_validate:", result_validate.content)
    create_log(f"result_with_validate: {result_validate.content}")
    return result_validate.content


# @tool
# def validate(a: str, b: str) -> str:
#     """Validate matching."""
#     util.print_colored_text(f"Validate matching: {a} and {b}", "cyan")
#     # tool function, do not use "" because the name will change to "Head_and_Neck."
#     prompt_validate_question = f"""Question: Is {a} equivalent to {b}?
#                             Context: {context}
#                             Answer the question within the context.
#                             Answer yes or no. Give a short explanation.
#                             """
#     result_validate = llm.invoke(prompt_validate_question)
#     print("result_validate:", result_validate.content)
#     create_log(f"result_with_validate: {result_validate.content}")
#     return result_validate.content


matching_tools = [syntactic, lexical, semantic, init, validate, merge]


def matching_tool_chain(model_output):
    tool_map = {tool.name: tool for tool in matching_tools}
    chosen_tool = tool_map[model_output["name"]]
    return itemgetter("arguments") | chosen_tool


def create_tool_use_agent(tools, tool_chain):
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
    # check similarity: update parameter1 based on provided arguments
    if len(sys.argv) > 1:
        similarity_threshold = float(sys.argv[1])
        alignment = alignment + "-" + sys.argv[1] + "-"
        predict_source_path_no_validation = config.predict_source_path_no_validation.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
        predict_target_path_no_validation = config.predict_target_path_no_validation.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
        predict_path_no_validation = config.predict_path_no_validation.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
        predict_source_path = config.predict_source_path.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
        predict_target_path = config.predict_target_path.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
        predict_path = config.predict_path.replace(".csv", "") + "-" + str(sys.argv[1]) + ".csv"
    print("similarity:", similarity_threshold)
    # can only calculate OpenAI models
    with get_openai_callback() as cb:
        # run matching agent
        chain = create_tool_use_agent(matching_tools, matching_tool_chain)
        response = chain.invoke({"input": "Ontology matching."})
        print("response:", response)
        # calculate cost
        print(f"total tokens: {cb.total_tokens}")
        print(f"prompt tokens: {cb.prompt_tokens}")
        print(f"completion tokens: {cb.completion_tokens}")
        print(f"total cost (USD): ${cb.total_cost}")
        # save cost
        print(util.calculate_cost(cb.total_tokens, cb.total_cost, cost_path, util.find_model_name(llm), alignment + "llm_with_matching_agent"))
