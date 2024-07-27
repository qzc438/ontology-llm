import run_config as config

llm = config.llm

# context learning
prompt = "What is the meaning of chair? Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "What is the meaning of chair in the context of conference? Give a short explanation."
print(llm.invoke(prompt).content)
# transitive reasoning
prompt = "Prompt: We know that paper is equivalent to submission, and submission is equivalent to contribution. Is paper equivalent to contribution? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
prompt = "Prompt: We know that meta-reviewer is the subclass of reviewer, and reviewer is the subclass of conference member. Is meta-reviewer the subclass of conference member? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
# self correction
prompt = "Prompt: We know that rejection is equivalent to submission, and submission is equivalent to contribution. Is rejection equivalent to contribution? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)
# the answer is not always "no"
prompt = "Prompt: We know that rejection is the subclass of meta-reviewer, and meta-reviewer is the subclass of reviwer. Is rejection the subclass of reviewer? Please answer yes or no. Give a short explanation."
print(llm.invoke(prompt).content)

# test sensitive word
# prompt = "Is clitoral gland equivalent to clitoris?"
# print(llm.invoke(prompt).content)
# prompt = "Refine matching for clitoral gland and clitoris"
# print(llm.invoke(prompt).content)

# test reverse order
# prompt = """Question: Is chairman equivalent to chair?
#         Context: conference
#         Answer the question within the context. Answer yes or no. Give a short explanation."""
# print(llm.invoke(prompt).content)
# prompt = """Question: Is chair equivalent to chairman?
#         Context: conference
#         Answer the question within the context. Answer yes or no. Give a short explanation."""
# print(llm.invoke(prompt).content)
