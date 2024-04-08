from langchain.prompts import PromptTemplate

prompt = PromptTemplate.from_template("What is a {adjective} name for a company that makes {product}?")

prompt.format(adjective="good", product="colorful socks")