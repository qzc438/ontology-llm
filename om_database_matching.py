import run_config as config
import util
import om_ontology_to_csv

import re
import logging
import pandas as pd
import collections
import json
import csv
import rdflib

import psycopg2
from pgvector.psycopg2 import register_vector

from langchain.agents import Tool
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent

# customer settings
o1_path = config.o1_path
o2_path = config.o2_path
align_path = config.align_path
context = config.context
o1_is_code = config.o1_is_code
o2_is_code = config.o2_is_code

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
context = config.context
# define result files
predict_source_path = config.predict_source_path
predict_target_path = config.predict_target_path
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
                      WHERE 1 - (embedding <=> '{content_embedding}') >%s
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
        create_log(f"matches: {matches}")
        # return matches
        return matches
    else:
        return None


def define_tools():
    tools = [
        Tool(
            name="initial_matching",
            func=initial_matching,
            description="useful for when you need initial matching."
        ),
        Tool(
            name="lexical_matching",
            func=lexical_matching,
            description="useful for when you need lexical matching."
        ),
        Tool(
            name="graphical_matching",
            func=graphical_matching,
            description="useful for when you need graphical matching."
        ),
        Tool(
            name="reciprocal_rank_fusion",
            func=reciprocal_rank_fusion,
            description="useful for when you need use reciprocal rank fusion."
        ),
        # Tool(
        #     name="ontology-matching",
        #     func=ontology_matching,
        #     description="useful for when you need to find equivalent matching."
        # ),
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


def reciprocal_rank_fusion(*rankings, b=60):
    reciprocal_ranks = collections.defaultdict(float)
    for i, ranking in enumerate(rankings):
        if ranking:
            for j, item in enumerate(ranking):
                reciprocal_rank = 1 / (j + 1)
                reciprocal_ranks[item] += reciprocal_rank
    fused_ranking = sorted(reciprocal_ranks.keys(), key=lambda item: reciprocal_ranks[item], reverse=True)
    return fused_ranking


# def ontology_matching(entity):
#     ranking1 = initial_matching(entity)
#     print(ranking1)
#     ranking2 = lexical_matching(entity)
#     print(ranking2)
#     ranking3 = graphical_matching(entity)
#     print(ranking3)
#     fused_ranking = reciprocal_rank_fusion(ranking1, ranking2, ranking3)
#     return fused_ranking


def extract_yes_no(text):
    match = re.search(r'\b(?:yes|no)\b', str(text), flags=re.IGNORECASE)
    return match.group().lower() if match else None


if __name__ == '__main__':

    # create logger
    logger = logging.getLogger('agent_log')
    # create file handler
    fileHandler = logging.FileHandler("agent.log", mode='w')
    fileHandler.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    # define llm
    llm = config.llm
    # define tools
    tools = define_tools()
    # define agents
    agent = define_agent(llm, tools)

    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
    e1_list = e1_list_class + e1_list_property
    e2_list = e2_list_class + e2_list_property

    # find entity matching
    util.create_document(predict_source_path, header=['Entity1', 'Entity2'])
    for entity in e1_list:
    # # for entity in ["http://cmt#Person"]:
    # # for entity in ["http://cmt#SubjectArea"]:
    # # for entity in ["http://cmt#Chairman"]:
    # # for entity in ["http://cmt#finalizePaperAssignment"]:
    # # for entity in ["http://confOf#Banquet"]:
        entity_name = om_ontology_to_csv.get_entity_name(entity, o1, o1_is_code)
        entity = util.uri_to_prefix_name(entity_name, "source")

        prompt_summary = f"Please find the equivalent entity to the following entity in the enclosed single quote: '{entity}' " \
                         "Use initial matching, lexical matching, and graphical matching. " \
                         "Format the output as JSON. Only contain the mathing results."

        result = agent({"input": prompt_summary})
        print(result['output'])
        # summary the matching
        output_json = json.loads(result['output'])
        initial_matching_result = output_json['initial_matching']
        lexical_matching_result = output_json['lexical_matching']
        graphical_matching_result = output_json['graphical_matching']
        predict_entity_list = reciprocal_rank_fusion(initial_matching_result, lexical_matching_result, graphical_matching_result)
        print("entity:", entity)
        print("predict_entity_list:", predict_entity_list)
        create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        # initial_matching_result = initial_matching(entity)
        # lexical_matching_result = lexical_matching(entity)
        # graphical_matching_result = graphical_matching(entity)
        # predict_entity_list = reciprocal_rank_fusion(initial_matching_result, lexical_matching_result, graphical_matching_result)
        # print("entity:", entity)
        # print("predict_entity_list:", predict_entity_list)
        # create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        # refine the matching, restrict to top_k for now
        for predict_entity in predict_entity_list[:top_k]:
            prompt_refine_question = (
                # Is Entity 1 different/distinct from Entity 2
                "Is {entity} equivalent to {predict_entity} in the context of {context}? Consider the meaning only."
                .format(context=context, entity=util.prefix_name_to_name(entity),
                        predict_entity=util.prefix_name_to_name(predict_entity)))
            result_refine = llm.predict(prompt_refine_question)
            print("result_refine", result_refine)
            create_log(f"prompt_refine_question: {prompt_refine_question}")
            create_log(f"result_refine: {result_refine}")
            if extract_yes_no(result_refine) == "yes":
                with open(predict_source_path, "a+", newline='') as f:
                    writer = csv.writer(f)
                    list_pair = [entity, predict_entity]
                    writer.writerow(list_pair)
                break

    # evaluation
    print(util.calculate_metrics(true_path, predict_source_path, config.alignment+"source", config.result_path))

    util.create_document(predict_target_path, header=['Entity2', 'Entity1'])
    for entity in e2_list:
        entity_name = om_ontology_to_csv.get_entity_name(entity, o2, o2_is_code)
        entity = util.uri_to_prefix_name(entity_name, "target")

        prompt_summary = f"Please find the equivalent entity to the following entity in the enclosed single quote: '{entity}' " \
                         "Use initial matching, lexical matching, and graphical matching. " \
                         "Format the output as JSON. Only contain the mathing results."

        result = agent({"input": prompt_summary})
        print(result['output'])
        # summary the matching
        output_json = json.loads(result['output'])
        initial_matching_result = output_json['initial_matching']
        lexical_matching_result = output_json['lexical_matching']
        graphical_matching_result = output_json['graphical_matching']
        predict_entity_list = reciprocal_rank_fusion(initial_matching_result, lexical_matching_result, graphical_matching_result)
        print("entity:", entity)
        print("predict_entity_list:", predict_entity_list)
        create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        # initial_matching_result = initial_matching(entity)
        # lexical_matching_result = lexical_matching(entity)
        # graphical_matching_result = graphical_matching(entity)
        # predict_entity_list = reciprocal_rank_fusion(initial_matching_result, lexical_matching_result, graphical_matching_result)
        # print("entity:", entity)
        # print("predict_entity_list:", predict_entity_list)
        # create_log(f"entity: {entity}, predict_entity_list: {predict_entity_list}")

        # refine the matching, restrict to top_k for now
        for predict_entity in predict_entity_list[:top_k]:
            prompt_refine_question = (
                # Is Entity 1 different/distinct from Entity 2
                "Is {entity} equivalent to {predict_entity} in the context of {context}? Consider the meaning only."
                .format(context=context, entity=util.prefix_name_to_name(entity),
                        predict_entity=util.prefix_name_to_name(predict_entity)))
            result_refine = llm.predict(prompt_refine_question)
            print("result_refine", result_refine)
            create_log(f"prompt_refine_question: {prompt_refine_question}")
            create_log(f"result_refine: {result_refine}")
            if extract_yes_no(result_refine) == "yes":
                with open(predict_target_path, "a+", newline='') as f:
                    writer = csv.writer(f)
                    list_pair = [entity, predict_entity]
                    writer.writerow(list_pair)
                break

    # evaluation
    print(util.calculate_metrics(true_path, predict_target_path, config.alignment+"target", config.result_path))

    df_source = pd.read_csv(config.predict_source_path)
    df_target = pd.read_csv(config.predict_target_path)
    df_merge = pd.merge(df_source, df_target, on=['Entity1', 'Entity2'])
    df_merge.to_csv(config.predict_path, index=False)

    print(util.calculate_metrics(config.true_path, config.predict_path, config.alignment, config.result_path))
