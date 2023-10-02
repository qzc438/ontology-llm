import dotenv
import os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI


def verbalise_sentence(input_file_path, output_file_path):
    # load openai API
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    # define chain
    llm = ChatOpenAI(temperature=0)

    prompt = PromptTemplate(
        input_variables=["sentence"],
        template="cmt: is the prefix of cmt ontology. "
                 "conference: is the prefix of conference ontology. "
                 "Please verbalise the statement {sentence}."
                 "Think step by step. Only answer verbalised sentence."
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    # generate results
    try:
        with open(input_file_path, "r") as input_file, open(output_file_path, "w") as output_file:
            for line in input_file:
                processed_line = chain.run(line)
                output_file.write(processed_line)
                output_file.write('\n')
        print(f"Processed lines written to '{output_file_path}'.")
    except FileNotFoundError:
        print(f"Input file '{input_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == '__main__':
    verbalise_sentence("rag/initial.txt", "rag/initial_verbalise.txt")
    verbalise_sentence("rag/graphical.txt", "rag/graphical_verbalise.txt")
    verbalise_sentence("rag/lexical.txt", "rag/lexical_verbalise.txt")
