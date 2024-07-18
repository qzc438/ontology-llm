import run_config as config

llm = config.llm

# test sensitive word
# prompt = "Is clitoral gland equivalent to Clitoris?"
# print(llm.invoke(prompt).content)
# prompt = "Refine matching for clitoral gland and Clitoris"
# print(llm.invoke(prompt).content)

prompt = """Question: Is chairman equivalent to chair? 
        Context: conference 
        Answer the question within the context. Answer yes or no. Give a short explanation."""
print(llm.invoke(prompt).content)

prompt = """Question: Is chair equivalent to chairman? 
        Context: conference 
        Answer the question within the context. Answer yes or no. Give a short explanation."""
print(llm.invoke(prompt).content)
