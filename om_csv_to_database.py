import time
import asyncio
from operator import itemgetter

import numpy as np
import pandas as pd

import asyncpg
from pgvector.asyncpg import register_vector

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, render_text_description

from langchain_community.callbacks import get_openai_callback

import run_config as config
import util


# load llm
llm = config.llm

# database connection
connection_string = config.connection_string

# null value
null_value_sentence = config.null_value_sentence

# load the csv file
df = pd.read_csv(config.csv_path)
# determine the number of digits needed
num_digits = len(str(df.index.max() + 1))
# create unique id column
df['entity_id'] = (df.index+1).astype(str).str.zfill(num_digits) + "-" + df['source_or_target'].astype(str) + "-" + df['entity_type'].astype(str) + "-" + df['entity'].apply(util.uri_to_name)
# remove null and duplicate
df = df.fillna('')
df.replace(null_value_sentence, "", inplace=True)
# df = df.drop_duplicates(subset='entity_id')
# # print
# print(df.head(5))
# print(df.tail(5))

# embedding settings
embeddings_service = config.embeddings_service
vector_length = config.vector_length

# calculate cost
cost_path = config.cost_path
alignment = config.alignment


# create traditional table
async def create_ontology_matching_table():
    # create connection
    conn = await asyncpg.connect(connection_string)
    # drop table if it already exists
    await conn.execute("DROP TABLE IF EXISTS ontology_matching CASCADE;")
    # create table schema
    await conn.execute('''CREATE TABLE ontology_matching
    (entity_id VARCHAR(1024) PRIMARY KEY, entity TEXT, source_or_target TEXT, entity_type TEXT, 
    syntactic_matching TEXT, lexical_matching TEXT, semantic_matching TEXT);''')
    # add csv data into table
    tuples = list(df.itertuples(index=False))
    await conn.copy_records_to_table(
        "ontology_matching", records=tuples, columns=list(df), timeout=10
    )
    # close connection
    await conn.close()


# create embedding table, solve the token issue
async def create_embedding_table(table_name):
    # define splitter
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[".", "\n"],
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
    )
    # define chunk
    chunked = []
    for index, row in df.iterrows():
        entity_id = row["entity_id"]
        matching = row[table_name]
        splits = text_splitter.create_documents([matching])
        for s in splits:
            r = {"entity_id": entity_id, "content": s.page_content}
            chunked.append(r)

    # retry failed API requests with exponential backoff
    def retry_with_backoff(func, *args, retry_delay=5, backoff_factor=2, **kwargs):
        max_attempts = 10
        retries = 0
        while retries <= max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"error: {e}")
                retries += 1
                wait = retry_delay * (backoff_factor ** retries)
                print(f"Retry after waiting for {wait} seconds...")
                time.sleep(wait)
        # max_attempts reached without success
        raise Exception("Max retry attempts exceeded without success")

    # generate results
    batch_size = 5
    for i in range(0, len(chunked), batch_size):
        request = [x["content"] for x in chunked[i: i + batch_size]]
        response = retry_with_backoff(embeddings_service.embed_documents, request)
        # store the retrieved vector embeddings for each chunk back
        for x, e in zip(chunked[i: i + batch_size], response):
            x["embedding"] = e
    # store the generated embeddings in a pandas dataframe
    matching_embeddings = pd.DataFrame(chunked)

    # create connection
    conn = await asyncpg.connect(connection_string)
    # add vector extension
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    await register_vector(conn)
    # drop table if exists
    await conn.execute(f"DROP TABLE IF EXISTS {table_name};")
    # create the embedding table to store vector embeddings
    sql = f'''CREATE TABLE {table_name}
    (entity_id VARCHAR(1024) NOT NULL REFERENCES ontology_matching(entity_id), content TEXT, embedding vector({vector_length}));'''
    await conn.execute(sql)
    # store all the generated embeddings back into the database
    for index, row in matching_embeddings.iterrows():
        await conn.execute(
            f"INSERT INTO {table_name} (entity_id, content, embedding) VALUES ($1, $2, $3);",
            row["entity_id"], row["content"], np.array(row["embedding"]),
        )
    await conn.close()


async def async_save_to_database():
    # create database
    await create_ontology_matching_table()
    await create_embedding_table("syntactic_matching")
    await create_embedding_table("lexical_matching")
    await create_embedding_table("semantic_matching")


@tool
def init() -> str:
    """Save ontology information."""
    util.print_colored_text("Save ontology information:", "blue")
    # create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # run the async_initialize_database coroutine using the event loop
    loop.run_until_complete(async_save_to_database())
    # close the loop
    loop.close()
    return "Save ontology information successfully."


database_tools = [init]


def database_tool_chain(model_output):
    tool_map = {tool.name: tool for tool in database_tools}
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
    # can only calculate OpenAI models
    with get_openai_callback() as cb:
        # run retrieval agent - Part 2
        chain = create_tool_use_agent(database_tools, database_tool_chain)
        response = chain.invoke({"input": "Save ontology information."})
        print("response:", response)
        # calculate cost
        print(f"total tokens: {cb.total_tokens}")
        print(f"prompt tokens: {cb.prompt_tokens}")
        print(f"completion tokens: {cb.completion_tokens}")
        print(f"total cost (USD): ${cb.total_cost}")
        # save cost
        print(util.calculate_cost(cb.total_tokens, cb.total_cost, cost_path, util.find_model_name(llm), alignment + "llm_with_retrieve_agent_2"))
