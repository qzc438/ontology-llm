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
alignment = "conference/cmt-conference/component/"

# o1_path = "anatomy/mouse-human-suite/component/source.xml"
# o2_path = "anatomy/mouse-human-suite/component/target.xml"
# align_path = "anatomy/mouse-human-suite/component/reference.xml"
# context = "anatomy"
# is_code = True

# common settings
data_folder = "data/" + alignment
o1_path = data_folder + "source.xml"
o2_path = data_folder + "target.xml"
align_path = data_folder + "reference.xml"
align_folder = "alignment/" + alignment
util.create_folder(align_folder)
csv_path = align_folder + "ontology_matching.csv"
predict_path = align_folder + "predict.csv"
true_path = align_folder + "true.csv"
result_path = "result.csv"

# load api
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# load api related components
llm = ChatOpenAI(model_name='gpt-4', temperature=0)
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
