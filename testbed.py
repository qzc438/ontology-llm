import config

llm = config.llm

# prompt = "Is http://cmt\#SubjectArea equivalent to http://conference\#Topic in the context of conference? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = "Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = "cmt: is the prefix of the CMT ontology and conference: is the prefix of the Conference ontology. Is cmt:SubjectArea equivalent to conference:Topic in the context of conference? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = "Is SubjectArea equivalent to Topic in the context of conference? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = "Is http://mouse.owl\#MA_0000270 equivalent to http://human.owl\#NCI_C33736 in the context of anatomy? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = "Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Please answer True if yes, answer False if no or unknown. Write a short explanation."
# prompt = " mouse: is the prefix of the Mouse ontology and human: is the prefix of the Human ontology. Is mouse:MA_0000270 equivalent to human:NCI_C33736 in the context of anatomy? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = " Is MA_0000270 equivalent to NCI_C33736 in the context of anatomy? Please answer True if yes, answer False if no or unknown. Write a short explanation."

# prompt = " Is subject area equivalent to topic? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "In the context of conference, is subject area equivalent to topic? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know A is equivalent to B. Is A equivalent to B? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know reviewer is equivalent to author. Is reviewer equivalent to author? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know A is equivalent to B, and B is equivalent to C. Is A equivalent to C? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know subject area is equivalent to topic, and topic is equivalent to abstract. Is subject area equivalent to abstract? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know A is the subclass of B, and C is the subclass of B. Is A equivalent to C? Please answer True if yes, False if not or unknown. Write a short explanation."
# prompt = "We know ConferenceParticipant is the subclass of conference, and conference_participant is the subclass of conference. Is ConferenceParticipant equivalent to confence_participant? Please answer True if yes, answer False if not or unknown. Write a short explanation."

# prompt = "Is small intestine equivalent to Small_Intestine in the context of anatomy? Consider the meaning only."
# prompt = "Is SubjectArea equivalent to topic in the context of conference? Consider the meaning only."
# prompt = "Is Person equivalent to Mouse in the context of conference? Consider the meaning only."
prompt = "Is Person equivalent to Person in the context of conference? Consider the meaning only."

print(llm.predict(prompt))
