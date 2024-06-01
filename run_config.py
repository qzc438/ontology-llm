import util
import rdflib
import dotenv
import os
import subprocess

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain_mistralai import ChatMistralAI
from langchain_community.chat_models import ChatOllama

from langchain_openai import OpenAIEmbeddings

# customer settings

# select llm

# load api key
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# # load GPT
llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
# llm = ChatOpenAI(model='gpt-4-turbo', temperature=0)
# # load MistralAI
# llm = ChatMistralAI(model="mistral-large-latest", temperature=0)
# # load Anthropic
# llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
# # load Gemini
# llm = ChatVertexAI(model="gemini-pro", temperature=0)

# # load Ollama
# llm = ChatOllama(model="llama3:8b", temperature=0)
# llm = ChatOllama(model="gemma:7b", temperature=0)
# llm = ChatOllama(model="wizardlm2:7b", temperature=0)
# llm = ChatOllama(model="phi3:3.8b", temperature=0)
# llm = ChatOllama(model="mistral:7b", temperature=0)


# # load llama3 variants
# llm = ChatOllama(model="llama3:text", temperature=0)
# llm = ChatOllama(model="llama3:instruct", temperature=0)

# the following models are currently not working
# # too slow
# llm = ChatOllama(model="llama3:70b", temperature=0)
# # pass argument value error: entity = str
# llm = ChatOllama(model="gemma:2b", temperature=0)
# # pass argument value error: entity = "John"
# llm = ChatOllama(model="llama2:7b", temperature=0)
# json.decoder.JSONDecodeError: Invalid \escape "http://mouse.owl#MA\_0000001"
# llm = ChatOllama(model="mixtral:8x7b", temperature=0) # MoE model
# json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes
# llm = ChatOllama(model="aya:8b", temperature=0) # multilingual models
# input only find "http://mouse.owl#MA_"
# llm = ChatOllama(model="stablelm2:12b", temperature=0) # multilingual models

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

# activate when execute run_conference_series
# if os.environ.get('alignment'):
#     alignment = os.environ['alignment']

# dbpedia result is not included in the paper
# alignment = "conference/dbpedia-confof/component/"
# alignment = "conference/dbpedia-ekaw/component/"
# alignment = "conference/dbpedia-sigkdd/component/"

# anatomy track
context = "anatomy"
o1_is_code = True
o2_is_code = True
alignment = "anatomy/mouse-human-suite/component/"

# food track
# context = "food nutritional composition"
# o1_is_code = True
# o2_is_code = True
# alignment = "food/ciqual-siren/component/"

# multifarm track
# context = "conference"
# o1_is_code = True
# o2_is_code = True
# alignment = "multifarm/cmt-cmt-cn-en/component/"

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

# path for matching without using agents
llm_only_path = align_folder + "llm_only.csv"

# reference file settings
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#Cell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity2')

# load ontology
o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"

# load embedding
embeddings_service = OpenAIEmbeddings()

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
        subprocess.run(["python", script])
