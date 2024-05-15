import os
import dotenv

from langchain_openai import ChatOpenAI

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
# llm = ChatOpenAI(model_name='gpt-4', temperature=0)

# ordering examples
prompt = "Entity 1: SubjectArea \n Entity 2: topic \n Question: Are these two entities equivalent? \n Context: Conference \n Answer the question within the context. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Entity 1: Person \n Entity 2: person \n Question: Are these two entities equivalent?. \n Context: Conference \n Answer the question within the context. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is SubjectArea equivalent to topic? \n Context: Conference \n Answer the question within the context. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is topic equivalent to SubjectArea? \n Context: Conference \n Answer the question within the context. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)

# llm matching examples
prompt = "Is http://cmt#SubjectArea equivalent to http://conference#Topic in the context of conference? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "cmt: is the prefix of the CMT ontology and conference: is the prefix of the Conference ontology. Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is SubjectArea equivalent to Topic in the context of conference? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is http://mouse.owl#MA_0000270 equivalent to http://human.owl#NCI_C33736 in the context of anatomy? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "mouse: is the prefix of the Mouse ontology and human: is the prefix of the Human ontology. Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is MA_0000270 equivalent to NCI_C33736 in the context of anatomy? Consider the meaning only."
print(llm.invoke(prompt).content)
prompt = "Is track equivalent to category? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is track equivalent to category in the context of conference? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know A is equivalent to B. Is A equivalent to B? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know paper is equivalent to author. Is paper equivalent to author in the context of conference? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know A is equivalent to B, and B is equivalent to C. Is A equivalent to C? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know subject area is equivalent to topic, and topic is equivalent to abstract. Is subject area equivalent to abstract in the context of conference? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know A is the subclass of B, and C is the subclass of B. Is A equivalent to C? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "We know artificial intelligence conference is the subclass of conference, and AI conference is the subclass of conference. Is artificial intelligence conference equivalent to AI conference in the context of conference? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)

# matching task testing
prompt = "Is \"Person in the context of conference\" equivalent to \"Person in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Chair in the context of conference\" equivalent to \"ConferenceChair in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"ConferenceChair in the context of conference\" equivalent to \"Chair in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"ConferenceChair in the context of conference\" equivalent to \"Chairman in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"SubjectArea in the context of conference\" equivalent to \"Topic in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Topic in the context of conference\" equivalent to \"SubjectArea in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Area in the context of materials science\" equivalent to \"Areain the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Power in the context of materials science\" equivalent to \"Power in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"SolidAngle in the context of materials science\" equivalent to \"SolidAngle in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"MagneticFluxDensity in the context of materials science\" equivalent to \"MagneticFluxDensity in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Momentum in the context of materials science\" equivalent to \"Momentum in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Permeability in the context of materials science\" equivalent to \"Permeability in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"FlowState in the context of materials science\" equivalent to \"State in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Substance in the context of materials science\" equivalent to \"ChemicalSubstance in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"small intestine in the context of anatomy\" equivalent to \"Small_Intestine in the context of anatomy\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Is \"Permeability in the context of anatomy\" equivalent to \"Permeability in the context of anatomy\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
