import time
import math
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


llm = config.llm
connection_string = config.connection_string
null_value_sentence = config.null_value_sentence
csv_path = config.csv_path

embeddings_service = config.embeddings_service
vector_length = config.vector_length

cost_path = config.cost_path
alignment = config.alignment

# batch settings
CSV_CHUNK_ROWS = 1000          # write 1000 lines each time
EMBED_BATCH = 32               # how many texts to embed per API call
DB_INSERT_BATCH = 1000         # how many DB rows per INSERT/COPY chunk


def retry_with_backoff(func, *args, retry_delay=5, backoff_factor=2, **kwargs):
    """Retry sync function calls (e.g., embed API) with exponential backoff."""
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
    raise Exception("Max retry attempts exceeded without success")


def _count_csv_rows(path: str) -> int:
    """Count data rows (excluding header) without loading file."""
    with open(path, "r", encoding="utf-8") as f:
        # subtract 1 for header
        return max(sum(1 for _ in f) - 1, 0)


def _clean_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """Apply your null/duplicate cleaning consistently."""
    df = df.fillna("")
    df.replace(null_value_sentence, "", inplace=True)
    return df


def _build_entity_id(chunk: pd.DataFrame, start_index: int, num_digits: int) -> pd.Series:
    """Create zero-padded entity_id based on running index and your fields."""
    # running row number within the whole file (1-based)
    seq = np.arange(start_index + 1, start_index + 1 + len(chunk))
    left = pd.Series(seq, index=chunk.index).astype(str).str.zfill(num_digits)
    return (
        left
        + "-" + chunk["source_or_target"].astype(str)
        + "-" + chunk["entity_type"].astype(str)
        + "-" + chunk["entity_uri"].apply(util.uri_to_name)
    )


# database
async def init_schema(conn: asyncpg.Connection):
    # clean create ontology table
    await conn.execute("DROP TABLE IF EXISTS ontology_matching CASCADE;")
    await conn.execute(
        """CREATE TABLE ontology_matching (
             entity_id VARCHAR(1024) PRIMARY KEY,
             entity_uri TEXT,
             source_or_target TEXT,
             entity_type TEXT,
             syntactic_matching TEXT,
             lexical_matching TEXT,
             semantic_matching TEXT
           );"""
    )

    # vector extension + register
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    await register_vector(conn)


async def create_embedding_table(conn: asyncpg.Connection, table_name: str):
    await conn.execute(f"DROP TABLE IF EXISTS {table_name};")
    await conn.execute(
        f"""CREATE TABLE {table_name} (
               entity_id VARCHAR(1024) NOT NULL REFERENCES ontology_matching(entity_id),
               content   TEXT,
               embedding VECTOR({vector_length})
            );"""
    )


async def load_ontology_matching_in_chunks():
    total_rows = _count_csv_rows(csv_path)
    num_digits = len(str(max(total_rows, 1)))

    # stream read in chunks of 1000 rows
    reader = pd.read_csv(csv_path, chunksize=CSV_CHUNK_ROWS)

    conn = await asyncpg.connect(connection_string)
    try:
        await init_schema(conn)

        processed = 0
        for chunk_idx, raw in enumerate(reader):
            # ensure expected columns and rename
            if "entity" in raw.columns and "entity_uri" not in raw.columns:
                raw.rename(columns={"entity": "entity_uri"}, inplace=True)

            # clean
            chunk = _clean_chunk(raw)

            # build entity_id with running global index
            chunk["entity_id"] = _build_entity_id(chunk, start_index=processed, num_digits=num_digits)

            # optional: dedup within chunk on entity_id
            # chunk = chunk.drop_duplicates(subset="entity_id", keep="first")

            # order columns to match ontology_matching schema
            cols = [
                "entity_id",
                "entity_uri",
                "source_or_target",
                "entity_type",
                "syntactic_matching",
                "lexical_matching",
                "semantic_matching",
            ]

            # fill missing with ""
            for c in cols:
                if c not in chunk.columns:
                    chunk[c] = ""

            # convert to tuples and write in DB_INSERT_BATCH sub-chunks
            tuples = list(chunk[cols].itertuples(index=False, name=None))
            for i in range(0, len(tuples), DB_INSERT_BATCH):
                sub = tuples[i : i + DB_INSERT_BATCH]
                await conn.copy_records_to_table(
                    "ontology_matching",
                    records=sub,
                    columns=cols,
                    timeout=60,
                )

            processed += len(chunk)
            print(f"[ontology_matching] wrote rows: {processed}/{total_rows}")

    finally:
        await conn.close()


async def load_embeddings_for_table(table_name: str):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[".", "\n"],
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
    )

    conn = await asyncpg.connect(connection_string)
    await register_vector(conn)
    try:
        await create_embedding_table(conn, table_name)

        # stream CSV again to avoid holding it all in memory
        reader = pd.read_csv(csv_path, chunksize=CSV_CHUNK_ROWS)

        # digit width again for consistent entity_id construction
        total_rows = _count_csv_rows(csv_path)
        num_digits = len(str(max(total_rows, 1)))
        processed_rows = 0
        inserted_vecs_total = 0

        # insert statement for execute
        insert_sql = f"INSERT INTO {table_name} (entity_id, content, embedding) VALUES ($1, $2, $3);"

        for chunk_idx, raw in enumerate(reader):
            # column normalization and cleaning
            if "entity" in raw.columns and "entity_uri" not in raw.columns:
                raw.rename(columns={"entity": "entity_uri"}, inplace=True)
            chunk = _clean_chunk(raw)
            # entity_id must match the ones inserted in ontology_matching
            chunk["entity_id"] = _build_entity_id(chunk, start_index=processed_rows, num_digits=num_digits)

            # build list of (entity_id, content) splits for this chunk
            to_embed: list[tuple[str, str]] = []
            for _, row in chunk.iterrows():
                entity_id = row["entity_id"]
                matching_text = row.get(table_name, "")
                # skip empties
                if not isinstance(matching_text, str) or matching_text.strip() == "":
                    continue
                docs = text_splitter.create_documents([matching_text])
                for d in docs:
                    to_embed.append((entity_id, d.page_content))

            # embed in EMBED_BATCH mini-batches
            embedded_records: list[tuple[str, str, np.ndarray]] = []
            for i in range(0, len(to_embed), EMBED_BATCH):
                batch_contents = [c for _, c in to_embed[i : i + EMBED_BATCH]]
                vectors = retry_with_backoff(embeddings_service.embed_documents, batch_contents)
                for (eid, content), vec in zip(to_embed[i : i + EMBED_BATCH], vectors):
                    embedded_records.append((eid, content, np.array(vec, dtype=np.float32)))

                # insert to DB in DB_INSERT_BATCH groups to cap memory/transactions
                if len(embedded_records) >= DB_INSERT_BATCH:
                    sub = embedded_records[:DB_INSERT_BATCH]
                    await conn.executemany(insert_sql, sub)
                    inserted_vecs_total += len(sub)
                    del embedded_records[:DB_INSERT_BATCH]
                    print(f"[{table_name}] inserted vectors: {inserted_vecs_total}")

            # flush any remainder for this chunk
            if embedded_records:
                await conn.executemany(insert_sql, embedded_records)
                inserted_vecs_total += len(embedded_records)
                embedded_records.clear()
                print(f"[{table_name}] inserted vectors: {inserted_vecs_total}")

            processed_rows += len(chunk)
            print(f"[{table_name}] processed source rows: {processed_rows}/{total_rows}")

    finally:
        await conn.close()


async def async_save_to_database():
    # base table in 1k-row chunks
    await load_ontology_matching_in_chunks()
    # embedding tables, each streamed & chunk-inserted
    await load_embeddings_for_table("syntactic_matching")
    await load_embeddings_for_table("lexical_matching")
    await load_embeddings_for_table("semantic_matching")


@tool
def init() -> str:
    """Save ontology information."""
    util.print_colored_text("Save ontology information:", "blue")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_save_to_database())
    loop.close()
    return "Save ontology information successfully."


database_tools = [init]


def database_tool_chain(model_output):
    tool_map = {tool.name: tool for tool in database_tools}
    chosen_tool = tool_map[model_output["name"]]
    return itemgetter("arguments") | chosen_tool


def create_tool_use_agent(tools, tool_chain):
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
    chain = prompt | llm | JsonOutputParser() | tool_chain
    return chain


if __name__ == "__main__":
    with get_openai_callback() as cb:
        chain = create_tool_use_agent(database_tools, database_tool_chain)
        response = chain.invoke({"input": "Save ontology information."})
        print("response:", response)
        print(f"total tokens: {cb.total_tokens}")
        print(f"prompt tokens: {cb.prompt_tokens}")
        print(f"completion tokens: {cb.completion_tokens}")
        print(f"total cost (USD): ${cb.total_cost}")
        print(
            util.calculate_cost(
                cb.total_tokens,
                cb.total_cost,
                cost_path,
                util.find_model_name(llm),
                alignment + "llm_with_retrieve_agent_2",
            )
        )