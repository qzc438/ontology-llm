import os
import dotenv
from langchain.chat_models import ChatOpenAI

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model_name='gpt-4', temperature=0)

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
prompt = "Is http://mouse.owl\#MA_0000270 equivalent to http://human.owl\#NCI_C33736 in the context of anatomy? Consider the meaning only."
print(llm.predict(prompt))
#
# prompt = "Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = " mouse: is the prefix of the Mouse ontology and human: is the prefix of the Human ontology. Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))
#
# prompt = " Is MA_0000270 equivalent to NCI_C33736 in the context of anatomy? Consider the meaning only."
# print(llm.predict(prompt))

# prompt = "Is track equivalent to category?"
# print(llm.predict(prompt))
# prompt = "Is track equivalent to category in the context of conference?"
# print(llm.predict(prompt))

# prompt = "We know A is equivalent to B. Is A equivalent to B?"
# print(llm.predict(prompt))
# prompt = "We know paper is equivalent to author. Is paper equivalent to author in the context of conference?"
# print(llm.predict(prompt))

# prompt = "We know A is equivalent to B, and B is equivalent to C. Is A equivalent to C?"
# print(llm.predict(prompt))
# prompt = "We know subject area is equivalent to topic, and topic is equivalent to abstract. Is subject area equivalent to abstract in the context of conference?"
# print(llm.predict(prompt))

# prompt = "We know A is the subclass of B, and C is the subclass of B. Is A equivalent to C?"
# print(llm.predict(prompt))
# prompt = "We know ConferenceParticipant is the subclass of conference, and conference_participant is the subclass of conference. Is ConferenceParticipant equivalent to confence_participant in the context of conference?"
# print(llm.predict(prompt))

# prompt = "Is small intestine equivalent to Small_Intestine in the context of anatomy? Consider the meaning only."
# prompt = "Is SubjectArea equivalent to topic in the context of conference? Consider the meaning only."
# prompt = "Is Person equivalent to Mouse in the context of conference? Consider the meaning only."
# prompt = "Is Person equivalent to Person in the context of conference? Consider the meaning only."
