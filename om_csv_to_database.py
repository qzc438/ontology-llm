import run_config as config
import util

import time
import numpy as np
import pandas as pd

import asyncio
import asyncpg
from pgvector.asyncpg import register_vector

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.tools import Tool

# null value
null_value = config.null_value

# load the csv file
df = pd.read_csv(config.csv_path)
# create id column
df['entity_id'] = df['source_or_target'].astype(str) + "-" + df['entity_type'].astype(str) + "-" + df['entity'].apply(util.uri_to_name)
# remove null and duplicate
df = df.fillna('')
df.replace(null_value, "", inplace=True)
df = df.drop_duplicates(subset='entity_id')
print(df.head(5))

# load llm
llm = config.llm

# database connection
connection_string = config.connection_string


def define_tools():
    tools = [
        Tool(
            name="save_csv_to_database",
            func=initialize_database,
            description="Useful for when you need save csv to database."
        ),
    ]
    return tools


def define_agent(llm, tools):
    agent = create_conversational_retrieval_agent(llm, tools, verbose=True)
    return agent


# create traditional table
async def create_ontology_matching_table():
    # create connection
    conn = await asyncpg.connect(connection_string)
    # drop table if it already exists
    await conn.execute("DROP TABLE IF EXISTS ontology_matching CASCADE;")
    # create table schema
    await conn.execute('''CREATE TABLE ontology_matching 
    (entity_id VARCHAR(1024) PRIMARY KEY, entity TEXT, source_or_target TEXT, entity_type TEXT, 
    syntactic_matching TEXT, lexical_matching TEXT, graphical_matching TEXT);''')
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
        for i in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"error: {e}")
                retries += 1
                wait = retry_delay * (backoff_factor ** retries)
                print(f"Retry after waiting for {wait} seconds...")
                time.sleep(wait)

    # generate results
    batch_size = 5
    for i in range(0, len(chunked), batch_size):
        request = [x["content"] for x in chunked[i: i + batch_size]]
        response = retry_with_backoff(config.embeddings_service.embed_documents, request)
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
    (entity_id VARCHAR(1024) NOT NULL REFERENCES ontology_matching(entity_id), content TEXT, embedding vector(1536));'''
    await conn.execute(sql)
    # store all the generated embeddings back into the database
    for index, row in matching_embeddings.iterrows():
        await conn.execute(
            f"INSERT INTO {table_name} (entity_id, content, embedding) VALUES ($1, $2, $3);",
            row["entity_id"], row["content"], np.array(row["embedding"]),
        )
    await conn.close()


async def async_initialize_database():
    # create database
    await create_ontology_matching_table()
    await create_embedding_table("syntactic_matching")
    await create_embedding_table("lexical_matching")
    await create_embedding_table("graphical_matching")


# create a variable to receive argument
def initialize_database(file):
    # create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # run the async_initialize_database coroutine using the event loop
    loop.run_until_complete(async_initialize_database())
    # close the loop
    loop.close()


if __name__ == '__main__':
    tools = define_tools()
    agent = define_agent(llm, tools)
    csv_name = config.csv_path
    prompt = f"Save {csv_name} to database."
    result = agent.invoke({"input": prompt})
