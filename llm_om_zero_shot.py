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
llm_zero_shot_path = config.llm_zero_shot_path
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
    with get_openai_callback() as cb:
        # find all entities
        e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
        e1_list = e1_list_class + e1_list_property
        e2_list = e2_list_class + e2_list_property
        # find entity matching
        util.create_document(llm_zero_shot_path, header=['Entity1', 'Entity2'])
        for e1 in e1_list:
            e1_name = om_ontology_to_csv.get_entity_name(e1, o1, o1_is_code)
            e1_name_clean = util.cleaning(e1_name)
            for e2 in e2_list:
                e2_name = om_ontology_to_csv.get_entity_name(e2, o2, o2_is_code)
                e2_name_clean = util.cleaning(e2_name)
                prompt_validate_question = f"""Entity1: {e1_name_clean} Entity2: {e2_name_clean}
                                        Question: Is Entity1 equivalent to Entity2?
                                        Answer yes or no. Give a short explanation.
                                        """
                response = llm.invoke(prompt_validate_question)
                print("response", response)
                # check answer
                answer = response.content
                if extract_yes_no(answer) == "yes":
                    with open(llm_zero_shot_path, "a+", newline='') as f:
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
        print(util.calculate_cost(cb.total_tokens, cb.total_cost, cost_path, util.find_model_name(llm), alignment + "LLM-Zero-Shot"))
        print(util.calculate_metrics(true_path, llm_zero_shot_path, result_path, util.find_model_name(llm), alignment + "LLM-Zero-Shot"))
