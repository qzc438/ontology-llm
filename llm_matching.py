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
