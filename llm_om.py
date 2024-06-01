import run_config as config
import om_ontology_to_csv
import util

import re
import csv

# customer settings
o1_path = config.o1_path
o2_path = config.o2_path
align_path = config.align_path
context = config.context
o1_is_code = config.o1_is_code
o2_is_code = config.o2_is_code

o1 = config.o1
o2 = config.o2
o1_prefix = config.o1_prefix
o2_prefix = config.o2_prefix

true_path = config.true_path
llm_only_path = config.llm_only_path
result_path = config.result_path

# define llm
llm = config.llm
# define alignment
alignment = config.alignment


def extract_yes_no(text):
    match = re.search(r'\b(?:yes|no)\b', str(text), flags=re.IGNORECASE)
    return match.group().lower() if match else None


if __name__ == '__main__':
    # find all entities
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = om_ontology_to_csv.find_all_entities()
    e1_list = e1_list_class + e1_list_property
    e2_list = e2_list_class + e2_list_property
    # find entity matching
    util.create_document(llm_only_path, header=['Entity1', 'Entity2'])
    for e1 in e1_list:
        e1_name = om_ontology_to_csv.get_entity_name(e1, o1, o1_is_code)
        entity_1 = util.uri_to_prefix_name(e1_name, "source")
        # refine the matching, restrict to top_k for now
        for e2 in e2_list:
            e2_name = om_ontology_to_csv.get_entity_name(e2, o2, o2_is_code)
            entity_2 = util.uri_to_prefix_name(e2_name, "target")
            prompt_refine_question = (
                "Is \"{entity_1} in the context of {context} \" equivalent to \"{entity_2} in the context of {context}\"? "
                "Consider only the meaning and not the formatting."
                "Answer yes or no. Give a short explanation."
                .format(context=context, entity_1=util.prefix_name_to_name(entity_1),
                        entity_2=util.prefix_name_to_name(entity_2)))
            result_refine = llm.invoke(prompt_refine_question).content
            print("result_refine", result_refine)
            if extract_yes_no(result_refine) == "yes":
                with open(llm_only_path, "a+", newline='') as f:
                    writer = csv.writer(f)
                    list_pair = [entity_1, entity_2]
                    writer.writerow(list_pair)
                break
    # evaluation
    print(util.calculate_metrics(true_path, llm_only_path, alignment + "llm", util.find_model_name(llm), result_path))
