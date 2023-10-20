import om_ontology_to_csv
import util
import csv
import re
import logging
import pandas as pd
import psycopg2
from pgvector.psycopg2 import register_vector
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent

# define generated variables
content = ""
source_or_target = ""
entity_type = ""
# define user variables
similarity_threshold = 0.8
num_matches = 50
# define result files
predict_path = "rag/predict.csv"
true_path = "rag/true.csv"


def create_log(message):
    logger = logging.getLogger('agent_log')
    logger.critical(message)


def entity_matching(entity, table_name):
    # create connection
    conn = psycopg2.connect('postgresql://postgres:postgres@127.0.0.1/ontology')
    register_vector(conn)
    # find content, source_or_target, entity_type
    cursor = conn.cursor()
    sql = f"select {table_name}, source_or_target, entity_type from ontology_matching where entity = (%s);"
    cursor.execute(sql, (entity,))
    result = cursor.fetchone()
    # set content value
    content = result[0]
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
    create_log(f"metadata: {content}, {source_or_target}, {entity_type}, {similarity_threshold}, {num_matches}")

    # embed the content
    embeddings_service = OpenAIEmbeddings()
    content_embedding = embeddings_service.embed_query(content)
    # find similar entities to the query using cosine similarity search
    # over all vector embeddings. This new feature is provided by `pgvector`.
    sql = f'''WITH vector_matches AS (
                  SELECT entity, 1 - (embedding <=> '{content_embedding}') AS similarity
                  FROM {table_name}
                  WHERE 1 - (embedding <=> '{content_embedding}') >%s
                  ORDER BY similarity DESC
                  LIMIT %s
                )
                SELECT o.entity, v.similarity as similarity FROM ontology_matching o, vector_matches v
                WHERE o.entity IN (SELECT entity FROM vector_matches)
                AND o.entity =  v.entity
                AND source_or_target = (%s) AND entity_type = (%s)'''
    cursor.execute(sql, (similarity_threshold, num_matches, source_or_target, entity_type))
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


def define_llm():
    llm = ChatOpenAI(temperature=0)
    return llm


def define_tools():
    tools = [
        Tool(
            name="initial-matching",
            func=initial_matching,
            description="useful for when you need initial matching."
        ),
        Tool(
            name="lexical-matching",
            func=lexical_matching,
            description="useful for when you need lexical matching."
        ),
        Tool(
            name="graphical-matching",
            func=graphical_matching,
            description="useful for when you need graphical matching."
        ),
    ]
    return tools


def define_agents(llm, tools):
    agent = create_conversational_retrieval_agent(llm, tools, verbose=True)
    # agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True)
    return agent


def initial_matching(entity):
    initial_matching = entity_matching(entity, "initial_matching")
    initial_matches = pd.DataFrame(initial_matching)
    initial_matches.drop_duplicates(['entity'], inplace=True)
    if len(initial_matches) != 0:
        return initial_matches['entity'].head(5).values.tolist()
    else:
        return None


def lexical_matching(entity):
    lexical_matching = entity_matching(entity, "lexical_matching")
    lexical_matches = pd.DataFrame(lexical_matching)
    lexical_matches.drop_duplicates(['entity'], inplace=True)
    if len(lexical_matches) != 0:
        return lexical_matches['entity'].head(5).values.tolist()
    else:
        return None


def graphical_matching(entity):
    graphical_matching = entity_matching(entity, "graphical_matching")
    graphical_matches = pd.DataFrame(graphical_matching)
    graphical_matches.drop_duplicates(['entity'], inplace=True)
    if len(graphical_matches) != 0:
        return graphical_matches['entity'].head(5).values.tolist()
    else:
        return None


def find_most_relevant_entity(sentence):
    pattern = r'\[(.*?)\]'
    match = re.search(pattern, sentence)
    if match:
        extracted_text = match.group(1)
        return extracted_text
    else:
        return None


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
    llm = define_llm()
    # define tools
    tools = define_tools()
    # define agents
    agent = define_agents(llm, tools)

    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
    e1_list = e1_list_class + e1_list_property
    # find entity matching
    util.create_document(predict_path, header=['Entity1', 'Entity2'])
    for entity in e1_list:
    # for entity in ["cmt:finalizePaperAssignment"]:
    # for entity in ["cmt:Person"]:
    # for entity in ["cmt:SubjectArea"]:
    # for entity in ["cmt:Chairman"]:
        entity = util.uri_to_prefix_name(entity, "source")
        prompt_summary = (f"What is equivalent to {entity}? "
                          f"Consider initial matching, lexical matching, and graphical matching."
                          f"Select the most relevant one. "
                          f"Answer only the most relevant one in [].")
        result = agent({"input": prompt_summary})
        create_log(result['output'])
        predict_entity = find_most_relevant_entity(result['output'])
    #     # check initial matching
    #     prompt_initial = f"What is equivalent to {entity}? Consider initial matching."
    #     result_initial = agent({"input": prompt_initial})
    #     # check lexical matching
    #     prompt_lexical = f"What is equivalent to {entity}? Consider lexical matching."
    #     result_lexical = agent({"input": prompt_lexical})
    #     # check graphical matching
    #     prompt_graphical = f"What is equivalent to {entity}? Consider graphical matching."
    #     result_graphical = agent({"input": prompt_graphical})
    #     # summarise the result
    #     prompt_summary = f"Select the most relevant one."\
    #                      "answer: most relevant one."\
    #                      "Format the output as JSON with the following key: answer"
    #     result = agent({"input": prompt_summary})
        # show results
        create_log(f"entity: {entity}, predict_entity: {predict_entity}")
        if predict_entity:
            # refine the matching, a new chain
            prompt_refine_question = (
                "Is {entity} similar to {predict_entity} in the context of research conference? Note {entity} is similar to {predict_entity} if they exactly match."
                .format(entity=util.prefix_name_to_name(entity), predict_entity=util.prefix_name_to_name(predict_entity)))
            result_refine = llm.predict(prompt_refine_question)
            create_log(f"prompt_refine_question: {prompt_refine_question}")
            create_log(f"result_refine: {result_refine}")
            if extract_yes_no(result_refine) == "yes":
                with open(predict_path, "a+", newline='') as f:
                    writer = csv.writer(f)
                    list_pair = [entity, predict_entity]
                    writer.writerow(list_pair)

    # evaluation
    print(util.calculate_metrics(true_path, predict_path))

# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())

# async def main():
#     # find all entities
#     e1_list_class, e2_list_class, e1_list_property, e2_list_property = ontology_to_csv.find_all_entities()
#     e1_list = e1_list_class + e1_list_property
#     # find entity matching
#     predict_path = "rag/predict.csv"
#     util.create_document(predict_path, header=['Entity1', 'Entity2'])
#
# for entity in e1_list:
#     print("entity", entity)
#     initial_matching = await entity_matching(entity, "initial_matching")
#     lexical_matching = await entity_matching(entity, "lexical_matching")
#     graphical_matching = await entity_matching(entity, "graphical_matching")
#     initial_matches = pd.DataFrame(initial_matching)
#     initial_matches.drop_duplicates(['entity'], inplace=True)
#     lexical_matches = pd.DataFrame(lexical_matching)
#     lexical_matches.drop_duplicates(['entity'], inplace=True)
#     graphical_matches = pd.DataFrame(graphical_matching)
#     graphical_matches.drop_duplicates(['entity'], inplace=True)
#
#     merged_df = initial_matches
#     if lexical_matches.empty:
#         merged_df = merged_df.copy()
#         merged_df['lexical_matching'] = np.nan
#     else:
#         merged_df = pd.merge(merged_df, lexical_matches, on='entity', how='outer')
#     if graphical_matches.empty:
#         merged_df = merged_df.copy()
#         merged_df['graphical_matching'] = np.nan
#     else:
#         merged_df = pd.merge(merged_df, graphical_matches, on='entity', how='outer')
#
#     merged_df.fillna(0, inplace=True)
#     merged_df['overall_matching'] = merged_df[
#         ['initial_matching', 'lexical_matching', 'graphical_matching']].mean(axis=1)
#     merged_df.sort_values(by=['overall_matching'], ascending=False, inplace=True)
#     predict_entity = merged_df['entity'].head(1).values[0]
#     print(entity, predict_entity)
#     with open(predict_path, "a+", newline='') as f:
#         writer = csv.writer(f)
#         list_pair = [entity, predict_entity]
#         writer.writerow(list_pair)
# # evaluation
# true_path = "rag/true.csv"
# print(util.calculate_metrics(true_path, predict_path))
