import util
import rdflib
import dotenv
import os
import subprocess
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# customer settings

is_code = False
context = "conference"
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

# alignment = "conference/dbpedia-confof/component/"


# is_code = True
# context = "anatomy"
# alignment = "anatomy/mouse-human-suite/component/"

is_code = True
context = "material sciences and engineering"
alignment = "mse/MaterialInformation-EMMO/component/"

# common settings
data_folder = "data/" + alignment
o1_path = data_folder + "source.xml"
o2_path = data_folder + "target.xml"
align_path = data_folder + "reference.xml"
align_folder = "alignment/" + alignment
util.create_folder(align_folder)
csv_path = align_folder + "ontology_matching.csv"
predict_source_path = align_folder + "predict_source.csv"
predict_target_path = align_folder + "predict_target.csv"
predict_path = align_folder + "predict.csv"
true_path = align_folder + "true.csv"
result_path = "result.csv"

o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"

# load api
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# load api related components
llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
embeddings_service = OpenAIEmbeddings()

# mapping settings
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

# search settings
similarity_threshold = 0.8
num_matches = 50
top_k = 5

if __name__ == '__main__':
    script_sequence = [
        "om_ontology_to_csv.py",
        "om_csv_to_database.py",
        "om_database_matching.py",
    ]
    for script in script_sequence:
        subprocess.run(["python", script])
