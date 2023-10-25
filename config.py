import rdflib
import dotenv
import os

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# customer settings
o1_path = "cmt-conference/component/source.xml"
o2_path = "cmt-conference/component/target.xml"
align_path = "cmt-conference/component/reference.xml"
context = "conference"
is_code = False

# o1_path = "anatomy/mouse-human-suite/component/source.xml"
# o2_path = "anatomy/mouse-human-suite/component/target.xml"
# align_path = "anatomy/mouse-human-suite/component/reference.xml"
# context = "anatomy"


# load api
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# load api related components
llm = ChatOpenAI(model_name='gpt-4', temperature=0)
embeddings_service = OpenAIEmbeddings()

# mapping settings
predict_path = "rag/predict.csv"
true_path = "rag/true.csv"
alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

# search settings
similarity_threshold = 0.8
num_matches = 50
top_k = 5

# intermediate csv file
csv_path = "ontology_matching.csv"
