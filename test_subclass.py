from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3:8b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0) # top_p is ignored if top_k=1
response = llm.invoke("A is the subclass of B. B is the subclass of A. What is the relationship of A and B in ontology matching?")
print(response.content)