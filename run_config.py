import os
import subprocess

import rdflib
import dotenv

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

import time
import csv
import util


def find_file(data_folder, base_name, extensions=("xml", "rdf", "owl")):
    for ext in extensions:
        path = os.path.join(data_folder, f"{base_name}.{ext}")
        if os.path.exists(path):
            return path
    return None


# customer settings

# select llm
# load api key
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# # load GPT, default timeout = None, do not have top_k setting
# llm = ChatOpenAI(model_name='gpt-4o-2024-05-13', temperature=0.0, seed=42, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0)
llm = ChatOpenAI(model_name='gpt-4o', temperature=0.0, seed=42, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0)
# llm = ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0.0, seed=42, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0)
# llm = ChatOpenAI(model_name='gpt-4o-mini', temperature=0.0, seed=42, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0)
# # load Anthropic, default timeout = None
# llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0) # expensive
# llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.0, seed=42, top_p=1.0, top_k=1, presence_penalty=0.0, frequency_penalty=0.0)
# llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.0, seed=42, top_p=1.0, top_k=1, presence_penalty=0.0, frequency_penalty=0.0)
# # load Llama 3
# llm = ChatOllama(model="llama3:8b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0) # top_p is ignored if top_k=1
# llm = ChatOllama(model="llama3.1:8b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)
# # load Qwen
# llm = ChatOllama(model="qwen2:7b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)
# llm = ChatOllama(model="qwen2.5:7b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)
# # load Gemma
# llm = ChatOllama(model="gemma2:9b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)
# # load GLM
# llm = ChatOllama(model="glm4:9b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)

# # load other models
# # load Mistral, default timeout = 120 is too short
# llm = ChatMistralAI(model="mistral-large-2407", temperature=0, timeout=1200)
# llm = ChatMistralAI(model="mistral-medium-2312", temperature=0) # will soon be deprecated
# llm = ChatMistralAI(model="mistral-small-2409", temperature=0, timeout=1200)
# # load Mistral open-source
# llm = ChatOllama(model="mistral-large:123b", temperature=0) # same to mistral-large-2407
# llm = ChatOllama(model="mistral-small:22b", temperature=0) # same to mistral-small-2409
# llm = ChatOllama(model="mistral-nemo:12b", temperature=0) # same to mistral-nemo-2407
# # load Yi
# llm = ChatOllama(model="yi:9b", temperature=0)
# # load Hermes
# llm = ChatOllama(model="hermes3:8b", temperature=0)

# # reasoning models
# llm = ChatOllama(model="deepseek-r1:8b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0, reasoning=False)
# llm = ChatOllama(model="gpt-oss:20b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0, reasoning=False)

# embedding settings
embeddings_service = OpenAIEmbeddings(model="text-embedding-ada-002")
# embeddings_service = OpenAIEmbeddings(model="text-embedding-3-small")
vector_length = 1536
# embeddings_service = OpenAIEmbeddings(model="text-embedding-3-large")
# vector_length = 3072
# embeddings_service = OllamaEmbeddings(model="llama3:8b")
# vector_length = 4096

# search settings
similarity_threshold = 0.90
top_k = 3
num_matches = 50

# alignment settings

# conference track
# context = "conference"
# o1_is_code = False
# o2_is_code = False
# alignment = "conference/cmt-conference/component/"
# alignment = "conference/cmt-confof/component/"
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

# activate when execute run_series_conference.py
# if os.environ.get('alignment'):
#     alignment = os.environ['alignment']

# dbpedia result is not included in the paper because we cannot find OAEI 2023 benchmarks
# 2022 results: https://oaei.ontologymatching.org/2022/results/conference/index.html#dbpedia
# 2023 results: https://oaei.ontologymatching.org/2023/results/conference/index.html
# alignment = "conference/dbpedia-confof/component/"
# alignment = "conference/dbpedia-ekaw/component/"
# alignment = "conference/dbpedia-sigkdd/component/"

# anatomy track
context = "anatomy"
o1_is_code = True
o2_is_code = True
alignment = "anatomy/mouse-human-suite/component/"

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

# mse Test Case 2
# context = "materials science"
# alignment = "mse/MaterialInformation-MatOnto/component/"
# o1_is_code = False
# o2_is_code = False

# mse Test Case 3
# context = "materials science"
# alignment = "mse/MaterialInformation-EMMO/component/"
# o1_is_code = False
# o2_is_code = True

# multilingual datasets

# multifarm track
# context = "conference"
# o1_is_code = True
# o2_is_code = True
# alignment = "multifarm/cmt-cmt-cn-en/component/"

# activate when execute run_series_multifarm.py
# if os.environ.get('alignment'):
#     alignment = os.environ['alignment']

# archaeology track
# context = "archaeology"
# alignment = "archaeology/de-en/component/"
# o1_is_code = True
# o2_is_code = True

# activate when execute run_series_archaeology.py
# if os.environ.get('alignment'):
#     alignment = os.environ['alignment']

# ce track
# context = "circular economy"
# alignment = "ce/ceon-bionto/component/"
# alignment = "ce/ceon-matonto/component/"
# o1_is_code = False
# o2_is_code = False

# dh track
# context = "digial humanities"
# alignment = "dh/defc-pactols/component/"
# alignment = "dh/dha-unesco/component/"
# alignment = "dh/idai-pactols/component/"
# alignment = "dh/idai-parthenos/component/"
# alignment = "dh/ironagedanube-pactols/component/"
# alignment = "dh/oeai-parthenos/component/"
# alignment = "dh/pactols-parthenos/component/"
# alignment = "dh/tadirah-unesco/component/"
# o1_is_code = True
# o2_is_code = True

# large datasets

# bio-ml track
# context = "biomedical"
# alignment = "bio-ml/ncit-doid/component/" # large
# alignment = "bio-ml/omim-ordo/component/" # large
# alignment = "bio-ml/snomed-fma.body/component/" # very large
# alignment = "bio-ml/snomed-ncit.neoplas/component/" # large
# alignment = "bio-ml/snomed-ncit.pharm/component/" # large
# o1_is_code = True
# o2_is_code = True

# e1_list_class: 15762
# e2_list_class: 8465
# e1_list_property: 97
# e2_list_property: 15

# e1_list_class: 9648
# e2_list_class: 9275
# e1_list_property: 0
# e2_list_property: 24

# e1_list_class: 34418
# e2_list_class: 88955
# e1_list_property: 136
# e2_list_property: 167

# e1_list_class: 22971
# e2_list_class: 20247
# e1_list_property: 136
# e2_list_property: 97

# e1_list_class: 29500
# e2_list_class: 22136
# e1_list_property: 136
# e2_list_property: 97

# biodiv track
# context = "biodiversity and ecology"
# alignment = "biodiv/envo-sweet/component/"
# o1_is_code = True
# o2_is_code = False

# context = "biodiversity and ecology"
# alignment = "biodiv/fish-zooplankton/component/"
# alignment = "biodiv/macroalgae-macrozoobenthos/component/"
# alignment = "biodiv/taxrefldAnimalia-ncbitaxonAnimalia/component/" # very large
# alignment = "biodiv/taxrefldBacteria-ncbitaxonBacteria/component/"
# alignment = "biodiv/taxrefldChromista-ncbitaxonChromista/component/"
# alignment = "biodiv/taxrefldFungi-ncbitaxonFungi/component/" # large
# alignment = "biodiv/taxrefldPlantae-ncbitaxonPlantae/component/" # large
# alignment = "biodiv/taxrefldProtozoa-ncbitaxonProtozoa/component/"
# o1_is_code = True
# o2_is_code = True

# common settings

# folder settings
data_folder = "data/" + alignment
o1_path = find_file(data_folder, "source")
o2_path = find_file(data_folder, "target")
align_path = find_file(data_folder, "reference")
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
llm_only_path = align_folder + "llm_only.csv"
llm_with_context_path = align_folder + "llm_with_context.csv"

# reference file settings
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#Cell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity2')
alignRelation = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#relation')

# load ontology
o1 = rdflib.Graph().parse(o1_path)
o2 = rdflib.Graph().parse(o2_path)

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
    # run script sequence and log time in milliseconds
    total_start = time.perf_counter()
    # check file exists
    file_exists = os.path.isfile("time.csv")
    # open CSV in append mode
    with open("time.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # write header only if file does not exist or is empty
        if not file_exists or os.stat("time.csv").st_size == 0:
            writer.writerow(["LLM", "Alignment", "Retrieving", "Embedding", "Matching", "Total"])
        # store times in order
        times = []
        # calculate time for each script
        for script in script_sequence:
            start = time.perf_counter()
            try:
                subprocess.run(["python", script], check=True)
            except subprocess.CalledProcessError as error:
                print(f"Error running {script}: {error}")
                times.append("ERROR")
                continue
            end = time.perf_counter()
            elapsed_ms = (end - start) * 1000
            print(f"Running time for {script}: {elapsed_ms:.2f} ms")
            times.append(f"{elapsed_ms:.2f}")
        # calculate total time
        total_end = time.perf_counter()
        total_elapsed_ms = (total_end - total_start) * 1000
        print(f"\nTotal running time: {total_elapsed_ms:.2f} ms")
        # make sure list length = 3, fill with empty if fewer scripts
        while len(times) < 3:
            times.append("")
        # append a row with metadata + times
        writer.writerow([util.find_model_name(llm), alignment, *times, f"{total_elapsed_ms:.2f}"])