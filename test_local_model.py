from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from langchain.llms import HuggingFacePipeline
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, AutoModelForSeq2SeqLM

print(torch.cuda.is_available())

os.environ['HUGGINGFACEHUB_API_TOKEN'] = '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'

question = "Who won the FIFA World Cup in the year 1994? "

template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

# repo_id = "google/flan-t5-xxl"
#
# llm = HuggingFaceHub(
#     repo_id=repo_id, model_kwargs={"temperature": 0.5, "max_length": 64}
# )
# llm_chain = LLMChain(prompt=prompt, llm=llm)
#
# print(llm_chain.run(question))

model_id = 'google/flan-t5-large'# go for a smaller model if you dont have the VRAM
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id, load_in_8bit=True)

pipe = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=100
)

local_llm = HuggingFacePipeline(pipeline=pipe)

print(local_llm('What is the capital of France? '))

llm_chain = LLMChain(prompt=prompt,
                     llm=local_llm
                     )

question = "What is the capital of England?"

print(llm_chain.run(question))
