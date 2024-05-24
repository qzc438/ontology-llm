import run_config as config
import om_ontology_to_csv
import util

import sys
import re
import logging
import pandas as pd
import collections
import csv
import itertools

import psycopg2
from pgvector.psycopg2 import register_vector

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool, render_text_description
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough


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
o1_prefix = config.o1_prefix
o2_prefix = config.o2_prefix

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


def create_log(message):
    logger = logging.getLogger('agent_log')
    logger.setLevel(logging.INFO)
    logger.info(message)


# start entity matching tools
def find_entity_id(entity, source_or_target):
    conn = psycopg2.connect(connection_string)
    register_vector(conn)
    cursor = conn.cursor()
    sql = f'''SELECT o.entity_id FROM ontology_matching o
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
    sql = f'''SELECT o.entity FROM ontology_matching o
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
    # sql = f"select {table_name}, source_or_target, entity_type from ontology_matching where entity = (%s);"
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
        else:
            source_or_target = "Source"
        # set entity_type value
        if result[2] == "Class":
            entity_type = "Class"
        elif result[2] == "Property":
            entity_type = "Property"
        create_log(f"entity: {entity}, {source_or_target}, {entity_type}, {similarity_threshold}, {num_matches}")

        # find similar entities to the query using cosine similarity search
        # over all vector embeddings. This new feature is provided by `pgvector`.
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
    else:
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
    syntactic_prompt = f"Syntactic matching for {entity}"
    syntactic_matching = chain.invoke({"input": syntactic_prompt})
    lexical_prompt = f"Lexical matching for {entity}"
    lexical_matching = chain.invoke({"input": lexical_prompt})
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
            # if item == null_value:  # skip NULL values
            #     continue
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
    candidates_without_validation_and_merge = list()
    candidates_with_validation_and_merge = list()

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
                    # compare entity name
                    if util.cleaning(entity_name).casefold() == util.cleaning(predict_entity_name).casefold():
                        candidates_with_validation_and_merge.append(find_entity(predict_entity))
                        create_log(f"result_without_validate: {predict_entity_name}")
                        continue
                    else:
                        chain = create_tool_use_agent(matching_tools, matching_tool_chain)
                        validate_prompt = f"Validate matching for {entity_name} and {predict_entity_name}."
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
def ontology() -> str:
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
    # e1_list = ["http://cmt#printHardcopyMailingManifests"]
    # e1_list = ["http://cmt#Bid"] # test all null value
    # e1_list = ["http://cmt#Meta-Reviewer"] # test matching validator
    # e1_list = ["http://cmt#hasDecision"]
    # e1_list = ["http://cmt#PaperFullVersion"]
    # e1_list = ["http://mouse.owl#MA_0000013"] # test entity name
    # e1_list = ["http://mouse.owl#MA_0000096"] # test one null value
    # e1_list = ["http://mouse.owl#MA_0001017"] # test all null value
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
    # evaluation
    print(util.calculate_metrics(true_path, predict_source_path_no_validation, result_path, util.find_model_name(llm), alignment + "source_no_validation"))
    print(util.calculate_metrics(true_path, predict_source_path, result_path, util.find_model_name(llm), alignment + "source"))

    # find matching from target ontology
    util.create_document(predict_target_path_no_validation, header=['Entity2', 'Entity1'])
    util.create_document(predict_target_path, header=['Entity2', 'Entity1'])
    # e2_list = ["http://conference#Contribution_co-author"]
    # e2_list = ["http://conference#Conference"]  # test matching validator
    # e2_list = ["http://human.owl#NCI_C32727"] # test not a json format
    for entity in e2_list:
        print("entity2:", entity)
        entity_id = find_entity_id(entity, "Target")
        candidates_without_validation_and_merge, candidates_with_validation_and_merge = find_most_relevant_entity(
            entity_id, "Target")
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
    # evaluation
    print(util.calculate_metrics(true_path, predict_target_path_no_validation, result_path, util.find_model_name(llm), alignment + "target_no_validation"))
    print(util.calculate_metrics(true_path, predict_target_path, result_path, util.find_model_name(llm), alignment + "target"))

    # matching merge
    chain = create_tool_use_agent(matching_tools, matching_tool_chain)
    chain.invoke({"input": f"Merge matching."})

    return "Ontology matching successfully completed."


# start ontology refine tools
@tool
def merge():
    """Merge matching."""
    util.print_colored_text(f"Merge matching:", "cyan")
    # tool function
    # matching merge without validation
    df_source_no_validation = pd.read_csv(predict_source_path_no_validation)
    df_target_no_validation = pd.read_csv(predict_target_path_no_validation)
    df_merge_no_validation = pd.merge(df_source_no_validation, df_target_no_validation, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge_no_validation = df_merge_no_validation.drop_duplicates()
    df_merge_no_validation.to_csv(predict_path_no_validation, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path_no_validation, result_path, util.find_model_name(llm), alignment + "no_validation", ))
    # matching merge with validation
    df_source = pd.read_csv(predict_source_path)
    df_target = pd.read_csv(predict_target_path)
    df_merge = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge = df_merge.drop_duplicates()
    df_merge.to_csv(predict_path, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path, result_path, util.find_model_name(llm), alignment))


@tool
def validate(a: str, b: str) -> str:
    """Validate matching."""
    util.print_colored_text(f"Validate matching: {a} and {b}", "cyan")
    # tool function
    prompt_validate_question = f"""Question: Is {a} often used interchangeably with {b}?
                            Context: {context}
                            Answer the question within the context.
                            Answer yes or no. Give a short explanation.
                            """
    result_validate = llm.invoke(prompt_validate_question).content
    print("result_validate:", result_validate)
    create_log(f"result_with_validate: {result_validate}")
    return result_validate


matching_tools = [syntactic, lexical, semantic, ontology, validate, merge]


def matching_tool_chain(model_output):
    tool_map = {tool.name: tool for tool in matching_tools}
    chosen_tool = tool_map[model_output["name"]]
    return itemgetter("arguments") | chosen_tool


def create_tool_use_agent(tools, tool_chain):
    # define combined prompt
    rendered_tools = render_text_description(tools)
    system_prompt = f"""You are an assistant that has access to the following set of tools. Here are the names and descriptions for each tool:
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
    # run matching agent
    chain = create_tool_use_agent(matching_tools, matching_tool_chain)
    chain.invoke({"input": f"Ontology matching."})
