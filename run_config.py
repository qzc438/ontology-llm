import os
import subprocess

import rdflib
import dotenv

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_community.chat_models import ChatOllama

from langchain_openai import OpenAIEmbeddings

import util

# customer settings

# select llm
# load api key
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# # load GPT, default timeout = None
# llm = ChatOpenAI(model_name='gpt-4-turbo-2024-04-09', temperature=0) # expensive
llm = ChatOpenAI(model_name='gpt-4o-2024-05-13', temperature=0)
# llm = ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0)
# llm = ChatOpenAI(model_name='gpt-3.5-turbo-0125', temperature=0)
# # load Anthropic, default timeout = None
# llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0) # expensive
# llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
# llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
# # load Mistral, default timeout = 120 is too short
# llm = ChatMistralAI(model="mistral-large-2402", temperature=0, timeout=1200)
# llm = ChatMistralAI(model="mistral-medium-2312", temperature=0) # will soon be deprecated
# llm = ChatMistralAI(model="mistral-small-2402", temperature=0)
# # load Mistral open-source
# llm = ChatOllama(model="mistral:7b", temperature=0)
# # load Llama 3
# llm = ChatOllama(model="llama3:8b", temperature=0)
# llm = ChatOllama(model="llama3.1:8b", temperature=0)
# # load Gemma
# llm = ChatOllama(model="gemma:7b", temperature=0)
# llm = ChatOllama(model="gemma2:9b", temperature=0)
# # load Qwen
# llm = ChatOllama(model="qwen2:7b", temperature=0)

# embedding settings
embeddings_service = OpenAIEmbeddings(model="text-embedding-ada-002")
# embeddings_service = OpenAIEmbeddings(model="text-embedding-3-small")
vector_length = 1536
# embeddings_service = OpenAIEmbeddings(model="text-embedding-3-large")
# vector_length = 3072

# search settings
similarity_threshold = 0.90
top_k = 3
num_matches = 50

# alignment settings
# conference track
context = "conference"
o1_is_code = False
o2_is_code = False
# alignment = "conference/cmt-conference/component/"
alignment = "conference/cmt-confof/component/"
# alignment = "conference/cmt-edas/component/"
# alignment = "conference/cmt-ekaw/component/"
# alignment = "conference/cmt-iasted/component/"
# alignment = "conference/cmt-sigkdd/component/"
# alignment = "conference/conference-confof/component/"
# alignment = "conference/conference-edas/component/"
# alignment = "conference/conference-ekaw/component/"
# alignment = "conference/conference-iasted/component/"
# alignment = "conference/conference-sigkdd/component/"
# alignment = "conference/confof-edas/component/"
# alignment = "conference/confof-ekaw/component/"
# alignment = "conference/confof-iasted/component/"
# alignment = "conference/confof-sigkdd/component/"
# alignment = "conference/edas-ekaw/component/"
# alignment = "conference/edas-iasted/component/"
# alignment = "conference/edas-sigkdd/component/"
# alignment = "conference/ekaw-iasted/component/"
# alignment = "conference/ekaw-sigkdd/component/"
# alignment = "conference/iasted-sigkdd/component/"

# activate when execute run_conference_series
# if os.environ.get('alignment'):
#     alignment = os.environ['alignment']

# multifarm track
# context = "conference"
# o1_is_code = True
# o2_is_code = True
# alignment = "multifarm/cmt-cmt-cn-en/component/"

# dbpedia result is not included in the paper because we cannot find OAEI 2023 benchmarks
# 2022 results: https://oaei.ontologymatching.org/2022/results/conference/index.html#dbpedia
# 2023 results: https://oaei.ontologymatching.org/2023/results/conference/index.html
# alignment = "conference/dbpedia-confof/component/"
# alignment = "conference/dbpedia-ekaw/component/"
# alignment = "conference/dbpedia-sigkdd/component/"

# anatomy track
# context = "anatomy"
# o1_is_code = True
# o2_is_code = True
# alignment = "anatomy/mouse-human-suite/component/"

# metadata
# e1_list_class: 2744
# e2_list_class: 3304
# e1_list_property: 3
# e2_list_property: 2

# mse track
# mse Test Case 1
# context = "materials science"
# alignment = "mse/MaterialInformationReduced-MatOnto/component/"
# o1_is_code = False
# o2_is_code = False

# metadata
# e1_list_class: 32
# e2_list_class: 847
# e1_list_property: 43
# e2_list_property: 95

# mse Test Case 2
# context = "materials science"
# alignment = "mse/MaterialInformation-MatOnto/component/"
# o1_is_code = False
# o2_is_code = False

# metadata
# e1_list_class: 545
# e2_list_class: 847
# e1_list_property: 98
# e2_list_property: 95

# mse Test Case 3
# context = "materials science"
# alignment = "mse/MaterialInformation-EMMO/component/"
# o1_is_code = False
# o2_is_code = True

# metadata
# e1_list_class: 545
# e2_list_class: 450
# e1_list_property: 98
# e2_list_property: 33

# common settings

# folder settings
data_folder = "data/" + alignment
o1_path = data_folder + "source.xml"
o2_path = data_folder + "target.xml"
align_path = data_folder + "reference.xml"
align_folder = "alignment/" + alignment
util.create_folder(align_folder)
csv_path = align_folder + "ontology_matching.csv"
predict_source_path_no_validation = align_folder + "predict_source_no_validation.csv"
predict_target_path_no_validation = align_folder + "predict_target_no_validation.csv"
predict_path_no_validation = align_folder + "predict_no_validation.csv"
predict_source_path = align_folder + "predict_source.csv"
predict_target_path = align_folder + "predict_target.csv"
predict_path = align_folder + "predict.csv"
true_path = align_folder + "true.csv"
result_path = "result.csv"
cost_path = "cost.csv"

# path for matching without using agents
llm_zero_shot_path = align_folder + "llm_zero_shot.csv"
llm_few_shot_path = align_folder + "llm_few_shot.csv"

# reference file settings
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#Cell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity2')

# load ontology
o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")

# database connection
connection_string = 'postgresql://postgres:postgres@127.0.0.1/ontology'

# handle null value in LLM
null_value_sentence = "Information is not available."
null_value_matching = "Entity-Dummy"
# null_value = "Dummy"
# null_value = "Placeholder"
# null_value = "N/A"
# null_value = "None"
# null_value = "Not Available"
# null_value = "Missing"

# calculate tokens
total_token_usage = 0


if __name__ == '__main__':
    # check metadata
    print("model_name:", util.find_model_name(llm))
    print("alignment:", alignment)
    print("similarity_threshold:", similarity_threshold)
    print()
    # define script sequence
    script_sequence = [
        "om_ontology_to_csv.py",
        "om_csv_to_database.py",
        "om_database_matching.py",
    ]
    for script in script_sequence:
        try:
            subprocess.run(["python", script], check=True)
        except subprocess.CalledProcessError as error:
            print(f"Error running {script}: {error}")
