### Test New LLMs:
```
# access limit
# from langchain_google_vertexai import ChatVertexAI
# llm = ChatVertexAI(model="gemini-pro", temperature=0)

# # pass argument value error: entity = str
# llm = ChatOllama(model="gemma:2b", temperature=0)

# # pass argument value error: entity = "John"
# llm = ChatOllama(model="llama2:7b", temperature=0)

# json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
# llm = ChatOllama(model="llama3:text", temperature=0)

# json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 2 column 5 (char 6)
# llm = ChatOllama(model="aya:8b", temperature=0) # multilingual model

# input only find "http://mouse.owl#MA_"
# llm = ChatOllama(model="stablelm2:12b", temperature=0) # multilingual model
# llm = ChatOllama(model="phi3:3.8b", temperature=0)

# init() need at least one argument, cannot handle no arguments
# llm = ChatOllama(model="wizardlm2:7b", temperature=0)

# "entity": "http://mouse.owl#MA\_0000010"
# llm = ChatOllama(model="mixtral:8x7b", temperature=0) # MoE model

# langchain_core.exceptions.OutputParserException: Invalid json output: I'm sorry but I do not have the capability to perform this task.
# llm = ChatOllama(model="llama3-groq-tool-use:8b", temperature=0)
```

### Test Matching Tasks:
```
# answer is not always "no"
prompt = """We know that rejection is the subclass of meta-reviewer, and meta-reviewer is the subclass of reviwer. 
            Is rejection the subclass of reviewer? 
            Please answer yes or no. Give a short explanation."""
print(llm.invoke(prompt).content)

# test sensitive word
prompt = "Is clitoral gland equivalent to clitoris?"
print(llm.invoke(prompt).content)
prompt = "Refine matching for clitoral gland and clitoris"
print(llm.invoke(prompt).content)

# test reverse order
prompt = """Question: Is chairman equivalent to chair?
            Context: conference
            Answer the question within the context. Answer yes or no. Give a short explanation."""
print(llm.invoke(prompt).content)
prompt = """Question: Is chair equivalent to chairman?
            Context: conference
            Answer the question within the context. Answer yes or no. Give a short explanation."""
print(llm.invoke(prompt).content)
```