import os
import dotenv
from langchain.chat_models import ChatOpenAI

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# llm = ChatOpenAI(model_name='gpt-4', temperature=0)
llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)

# prompt = "Is http://cmt#SubjectArea equivalent to http://conference#Topic in the context of conference? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = "Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = "cmt: is the prefix of the CMT ontology and conference: is the prefix of the Conference ontology. Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = "Is SubjectArea equivalent to Topic in the context of conference? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = "Is http://mouse.owl#MA_0000270 equivalent to http://human.owl#NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = "Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = " mouse: is the prefix of the Mouse ontology and human: is the prefix of the Human ontology. Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = " Is MA_0000270 equivalent to NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))

# prompt = "Is track equivalent to category? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
# prompt = "Is track equivalent to category in the context of conference? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "We know A is equivalent to B. Is A equivalent to B? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
# prompt = "We know paper is equivalent to author. Is paper equivalent to author in the context of conference? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "We know A is equivalent to B, and B is equivalent to C. Is A equivalent to C? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
# prompt = "We know subject area is equivalent to topic, and topic is equivalent to abstract. Is subject area equivalent to abstract in the context of conference? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "We know A is the subclass of B, and C is the subclass of B. Is A equivalent to C? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
# prompt = "We know artificial intelligence conference is the subclass of conference, and AI conference is the subclass of conference. Is artificial intelligence conference equivalent to AI conference in the context of conference? Please answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "Is small intestine equivalent to Small_Intestine in the context of anatomy? Consider the meaning only."
# prompt = "Is SubjectArea equivalent to topic?"
# prompt = "Is Person equivalent to Mouse in the context of conference?"
# prompt = "Is Person equivalent to Person?"

prompt = "Is \"Person in the context of conference\" equivalent to \"Person in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Chair in the context of conference\" equivalent to \"ConferenceChair in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"ConferenceChair in the context of conference\" equivalent to \"Chair in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"ConferenceChair in the context of conference\" equivalent to \"Chairman in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"SubjectArea in the context of conference\" equivalent to \"Topic in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Topic in the context of conference\" equivalent to \"SubjectArea in the context of conference\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Area in the context of materials science\" equivalent to \"Areain the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Power in the context of materials science\" equivalent to \"Power in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"SolidAngle in the context of materials science\" equivalent to \"SolidAngle in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"MagneticFluxDensity in the context of materials science\" equivalent to \"MagneticFluxDensity in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Momentum in the context of materials science\" equivalent to \"Momentum in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Permeability in the context of materials science\" equivalent to \"Permeability in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"FlowState in the context of materials science\" equivalent to \"State in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Substance in the context of materials science\" equivalent to \"ChemicalSubstance in the context of materials science\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"small intestine in the context of anatomy\" equivalent to \"Small_Intestine in the context of anatomy\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
prompt = "Is \"Permeability in the context of anatomy\" equivalent to \"Permeability in the context of anatomy\"? Consider only the context meaning and not the formatting. Answer yes or no. Give a short explanation."
print(llm.predict(prompt))
#
# prompt = "In the context of anatomy, is \"small intestine\" equivalent to \"Small_Intestine\"? Ignore the formatting. Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
#
# prompt = "In the context of material science, is \"Power\" equivalent to \"Power\"? Ignore the formatting. Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "In the context of conference, is \"Person\" equivalent to \"Person\"? Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "In the context of anatomy, is \"small intestine\" equivalent to \"Small_Intestine\"? Consider only the meaning and not the formatting. Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))
#
# prompt = "In the context of anatomy, is \"small intestine\" equivalent to \"SmallIntestine\"? Ignore the formatting. Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "In the context of materials science, is \"Power\" equivalent to \"Power\"? Consider only the meaning and not the formatting. Answer yes or no. Give a short explanation."
# print(llm.predict(prompt))

# prompt = "Normalise the following name \"ConventionalQuantitativeProperty\". Use white spaces to split compound words. Change uppercase to lowercase. Output the normalized form."
# print(llm.predict(prompt))

