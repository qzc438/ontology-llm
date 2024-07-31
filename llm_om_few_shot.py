import re
import csv

from langchain_community.callbacks import get_openai_callback

import run_config as config
import om_ontology_to_csv
import util


# customer settings
o1_path = config.o1_path
o2_path = config.o2_path
align_path = config.align_path
context = config.context
o1_is_code = config.o1_is_code
o2_is_code = config.o2_is_code

o1 = config.o1
o2 = config.o2

true_path = config.true_path
llm_few_shot_path = config.llm_few_shot_path
result_path = config.result_path
cost_path = config.cost_path

# define llm
llm = config.llm
# define alignment
alignment = config.alignment


def extract_yes_no(text):
    match = re.search(r'\b(?:yes|no)\b', str(text), flags=re.IGNORECASE)
    return match.group().lower() if match else None


if __name__ == '__main__':
    # can only calculate OpenAI models
    with get_openai_callback() as cb:
        # find all entities
        e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
        e1_list = e1_list_class + e1_list_property
        e2_list = e2_list_class + e2_list_property
        # find entity matching
        util.create_document(llm_few_shot_path, header=['Entity1', 'Entity2'])
        for e1 in e1_list:
            # define metadata
            om_ontology_to_csv.ontology = om_ontology_to_csv.o1
            om_ontology_to_csv.ontology_is_code = om_ontology_to_csv.o1_is_code
            # find information
            e1_syntactic = om_ontology_to_csv.syntactic(e1)
            e1_lexical = om_ontology_to_csv.lexical(e1)
            e1_semantic = om_ontology_to_csv.semantic(e1)
            print()
            for e2 in e2_list:
                # define metadata
                om_ontology_to_csv.ontology = om_ontology_to_csv.o2
                om_ontology_to_csv.ontology_is_code = om_ontology_to_csv.o2_is_code
                # find information
                e2_syntactic = om_ontology_to_csv.syntactic(e2)
                e2_lexical = om_ontology_to_csv.lexical(e2)
                e2_semantic = om_ontology_to_csv.semantic(e2)
                prompt_validate_question = f"""
                Question: Is Entity1 equivalent to Entity2? Consider the following:
                The syntactic information of Entity1: {e1_syntactic}
                The lexical information of Entity1: {e1_lexical}
                The semantic information of Entity1: {e1_semantic}
                The syntactic information of Entity2: {e2_syntactic}
                The lexical information of Entity2: {e2_lexical}
                The semantic information of Entity2: {e2_semantic}
                Answer yes or no. Give a short explanation.
                """
                response = llm.invoke(prompt_validate_question)
                # check answer
                answer = response.content
                print("answer:", answer)
                print()
                if extract_yes_no(answer) == "yes":
                    with open(llm_few_shot_path, "a+", newline='') as f:
                        writer = csv.writer(f)
                        list_pair = [e1, e2]
                        writer.writerow(list_pair)
                    break
        # calculate cost
        print(f"total tokens: {cb.total_tokens}")
        print(f"prompt tokens: {cb.prompt_tokens}")
        print(f"completion tokens: {cb.completion_tokens}")
        print(f"total cost (USD): ${cb.total_cost}")
        # evaluation
        print(util.calculate_cost(cb.total_tokens, cb.total_cost, cost_path, util.find_model_name(llm), alignment + "LLM-Few-Shot"))
        print(util.calculate_metrics(true_path, llm_few_shot_path, result_path, util.find_model_name(llm), alignment + "LLM-Few-Shot"))
