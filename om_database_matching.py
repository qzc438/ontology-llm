import run_config as config
import util
import om_ontology_to_csv

import sys
import re
import logging
import pandas as pd
import collections
import json
import csv

import psycopg2
from pgvector.psycopg2 import register_vector

from langchain.agents import Tool
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent

from itertools import groupby

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

# define entity metadata
content = ""
source_or_target = ""
entity_type = ""
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


def create_log(message):
    logger = logging.getLogger('agent_log')
    logger.critical(message)


def entity_matching(entity, table_name):
    # create connection
    conn = psycopg2.connect('postgresql://postgres:postgres@127.0.0.1/ontology')
    register_vector(conn)
    # find content, source_or_target, entity_type
    cursor = conn.cursor()
    sql = f'''select m.embedding, o.source_or_target, o.entity_type
              from ontology_matching o, {table_name} m
              where o.entity = m.entity
              and o.entity = (%s);'''
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
        else:
            entity_type = "Property"
        create_log(f"metadata: {entity}, {source_or_target}, {entity_type}, {similarity_threshold}, {num_matches}")

        # embeddings_service = config.embeddings_service
        # content_embedding = embeddings_service.embed_query(content)

        # find similar entities to the query using cosine similarity search
        # over all vector embeddings. This new feature is provided by `pgvector`.
        sql = f'''WITH vector_matches AS (
                      SELECT entity, 1 - (embedding <=> '{content_embedding}') AS similarity
                      FROM {table_name}
                      WHERE 1 - (embedding <=> '{content_embedding}') >= %s
                    )
                    SELECT o.entity, v.similarity as similarity FROM ontology_matching o, vector_matches v
                    WHERE o.entity IN (SELECT entity FROM vector_matches)
                    AND o.entity =  v.entity
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
        # return matches
        return matches
    else:
        return None


def define_tools():
    tools = [
        Tool(
            name="initial_matching",
            func=initial_matching,
            description="Useful for when you need initial matching."
        ),
        Tool(
            name="lexical_matching",
            func=lexical_matching,
            description="Useful for when you need lexical matching."
        ),
        Tool(
            name="graphical_matching",
            func=graphical_matching,
            description="Useful for when you need graphical matching."
        ),
    ]
    return tools


def define_agent(llm, tools):
    agent = create_conversational_retrieval_agent(llm, tools, verbose=True)
    return agent


def initial_matching(entity):
    initial_matching = entity_matching(entity, "initial_matching")
    initial_matches = pd.DataFrame(initial_matching)
    initial_matches.drop_duplicates(['entity'], inplace=True)
    if len(initial_matches) != 0:
        return initial_matches['entity'].head(top_k).values.tolist()
    else:
        return None


def lexical_matching(entity):
    lexical_matching = entity_matching(entity, "lexical_matching")
    lexical_matches = pd.DataFrame(lexical_matching)
    lexical_matches.drop_duplicates(['entity'], inplace=True)
    if len(lexical_matches) != 0:
        return lexical_matches['entity'].head(top_k).values.tolist()
    else:
        return None


def graphical_matching(entity):
    graphical_matching = entity_matching(entity, "graphical_matching")
    graphical_matches = pd.DataFrame(graphical_matching)
    graphical_matches.drop_duplicates(['entity'], inplace=True)
    if len(graphical_matches) != 0:
        return graphical_matches['entity'].head(top_k).values.tolist()
    else:
        return None


def find_all_matching_candidate(entity):
    prompt_summary = f"Please find the equivalent entity to the following entity enclosed by a pair of double quotes: \"{entity}\". " \
                     "Consider initial matching, lexical matching, and graphical matching. " \
                     "Format the output as JSON enclosed by a pair of curly braces with the following keys: initial_matching, lexical_matching, graphical_matching. " \
                     "Set value as a list if you find multiple matching results in initial matching, lexical matching, or graphical matching. "\
                     "Set a null value if you cannot find any matching results in initial matching, lexical matching, or graphical matching. " \
                     "Output the JSON only."
    print("matching prompt:", prompt_summary)
    # define tools
    tools = define_tools()
    # define agent
    agent = define_agent(llm, tools)
    # execute agent
    result = agent({"input": prompt_summary})
    print(result['output'])
    # summary the matching
    output_json = json.loads(result['output'])
    return output_json


def extract_yes_no(text):
    match = re.search(r'\b(?:yes|no)\b', str(text), flags=re.IGNORECASE)
    return match.group().lower() if match else None


def reciprocal_rank_fusion_all_with_grouped_scores_exclude_none(*rankings):
    reciprocal_ranks = collections.defaultdict(float)
    for ranking in rankings:
        if not isinstance(ranking, (list, tuple)):
            ranking = [ranking]
        for position, item in enumerate(ranking, start=1):
            if item is None:  # Skip None values
                continue
            reciprocal_ranks[item] += 1 / position
    # sort by reciprocal rank value, then by item lexicographically for tie-breaking
    fused_ranking_with_scores = sorted(reciprocal_ranks.items(), key=lambda x: (-x[1], x[0]))
    # group items by their score
    grouped_items_by_score = [(score, [item for item, _ in items]) for score, items in
                              groupby(fused_ranking_with_scores, key=lambda x: x[1])]
    return grouped_items_by_score


def find_most_relevant_entity(entity):

    candidates_without_validation_and_merge = list()
    candidates_with_validation_and_merge = list()

    # invoke find_all_matching_candidate
    output_json = find_all_matching_candidate(entity)
    # prepare rankings, wrapping string values in lists and filtering out None values
    rankings = [value if isinstance(value, list) else [value] for value in output_json.values() if value is not None]

    if rankings:
        # call the reciprocal rank fusion function with the processed rankings
        predict_entity_list = reciprocal_rank_fusion_all_with_grouped_scores_exclude_none(*rankings)
        print("entity:", entity)
        print("predict_entity_list:", predict_entity_list)
        create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        # without validation, select the first one
        scores, predict_entities = predict_entity_list[0]
        for predict_entity in predict_entities:
            candidates_without_validation_and_merge.append(predict_entity)

        # with validation
        for scores, predict_entities in predict_entity_list[:top_k]:
            # predict_entities.append("target:TieBreakingTest")
            for predict_entity in predict_entities:
                entity_name = util.prefix_name_to_name(entity)
                predict_entity_name = util.prefix_name_to_name(predict_entity)
                if util.cleaning(entity_name).casefold() == util.cleaning(predict_entity_name).casefold():
                    candidates_with_validation_and_merge.append(predict_entity)
                    continue
                else:
                    prompt_refine_question = (
                        "Is \"{entity_name} in the context of {context}\" equivalent to \"{predict_entity_name} in the context of {context}\"? "
                        "Consider only the context meaning and not the formatting."
                        "Answer yes or no. Give a short explanation."
                        .format(context=context, entity_name=entity_name, predict_entity_name=predict_entity_name))
                    result_refine = llm.predict(prompt_refine_question)
                    print("result_refine:", result_refine)
                    create_log(f"prompt_refine_question: {prompt_refine_question}")
                    create_log(f"result_refine: {result_refine}")

                    if extract_yes_no(result_refine) == "yes":
                        candidates_with_validation_and_merge.append(predict_entity)

            print("candidates_with_validation_and_merge:", candidates_with_validation_and_merge)
            if candidates_with_validation_and_merge:
                break

    return candidates_without_validation_and_merge, candidates_with_validation_and_merge


if __name__ == '__main__':

    # define llm
    llm = config.llm

    # create logger
    logger = logging.getLogger('agent_log')
    # create file handler
    fileHandler = logging.FileHandler("agent.log", mode='w')
    fileHandler.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    # update parameter1 based on provided arguments
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

    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
    e1_list = e1_list_class + e1_list_property
    e2_list = e2_list_class + e2_list_property

    # find entity matching
    util.create_document(predict_source_path_no_validation, header=['Entity1', 'Entity2'])
    util.create_document(predict_source_path, header=['Entity1', 'Entity2'])
    for entity in e1_list:
        entity_name = om_ontology_to_csv.get_entity_name(entity, o1, o1_is_code)
        entity = util.uri_to_prefix_name(entity_name, "source")
        candidates_without_validation_and_merge, candidates_with_validation_and_merge = find_most_relevant_entity(entity)
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
    print(util.calculate_metrics(true_path, predict_source_path_no_validation, alignment + "source_no_validation", result_path))
    print(util.calculate_metrics(true_path, predict_source_path, alignment + "source", result_path))

    util.create_document(predict_target_path_no_validation, header=['Entity2', 'Entity1'])
    util.create_document(predict_target_path, header=['Entity2', 'Entity1'])
    for entity in e2_list:
        entity_name = om_ontology_to_csv.get_entity_name(entity, o2, o2_is_code)
        entity = util.uri_to_prefix_name(entity_name, "target")
        candidates_without_validation_and_merge, candidates_with_validation_and_merge = find_most_relevant_entity(entity)
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
    print(util.calculate_metrics(true_path, predict_target_path_no_validation, alignment + "target_no_validation", result_path))
    print(util.calculate_metrics(true_path, predict_target_path, alignment + "target", result_path))

    df_source_no_validation = pd.read_csv(predict_source_path_no_validation)
    df_target_no_validation = pd.read_csv(predict_target_path_no_validation)
    df_merge_no_validation = pd.merge(df_source_no_validation, df_target_no_validation, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge_no_validation = df_merge_no_validation.drop_duplicates()
    df_merge_no_validation.to_csv(predict_path_no_validation, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path_no_validation, alignment + "no_validation", result_path))

    df_source = pd.read_csv(predict_source_path)
    df_target = pd.read_csv(predict_target_path)
    df_merge = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    # Remove any duplicate rows in the common
    df_merge = df_merge.drop_duplicates()
    df_merge.to_csv(predict_path, index=False)
    # evaluation
    print(util.calculate_metrics(true_path, predict_path, alignment, result_path))
