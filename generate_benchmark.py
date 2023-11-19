import util
import rdflib
import csv
import pandas as pd

alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')
alignRelation = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentrelation')

# o1_path = "data/anatomy/mouse-human-suite/component/source.xml"
# o2_path = "data/anatomy/mouse-human-suite/component/target.xml"

o1_path = "data/mse/MaterialInformation-EMMO/component/source.xml"
o2_path = "data/mse/MaterialInformation-EMMO/component/target.xml"

o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"

labelEntity = rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#prefLabel')


def get_entity_label(entity, ontology):
    entity_label = ""
    results_rdfs = set(ontology.triples((entity, rdflib.RDFS.label, None)))
    results_skos = set(ontology.triples((entity, labelEntity, None)))
    combined_results = results_rdfs.union(results_skos)
    for s, p, o in combined_results:
        entity_label = str(o)
    # print(entity_label)
    return entity_label


def get_entity_name(entity, ontology, entity_is_code):
    if entity_is_code:
        entity_name = get_entity_label(entity, ontology) or util.uri_to_name(entity)
    else:
        entity_name = util.uri_to_name(entity)
    return entity_name


def find_alignment(align_path, true_path, o1_is_code, o2_is_code):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # create true csv
    util.create_document(true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            relation = align.value(s, alignRelation, None)
            if str(relation) == "=":
                e1_uri = align.value(s, alignEntity1, None)
                e2_uri = align.value(s, alignEntity2, None)
                e1_name = get_entity_name(e1_uri, o1, o1_is_code)
                e2_name = get_entity_name(e2_uri, o2, o2_is_code)
                e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
                e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
                list_pair = [e1_prefix_name, e2_prefix_name]
                writer.writerow(list_pair)


def find_alignment_all(align_path, true_path, o1_is_code, o2_is_code):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # create true csv
    util.create_document(true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            e1_uri = align.value(s, alignEntity1, None)
            e2_uri = align.value(s, alignEntity2, None)
            e1_name = get_entity_name(e1_uri, o1, o1_is_code)
            e2_name = get_entity_name(e2_uri, o2, o2_is_code)
            e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
            e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
            list_pair = [e1_prefix_name, e2_prefix_name]
            writer.writerow(list_pair)


def normal_string(original_string):
    return original_string.replace('_', ' ').lower()


# def generate_filtered_csv(input_path, output_path):
#     df = pd.read_csv(input_path)
#     delimiter = ':'
#     df['Entity1_Normal'] = df['Entity1'].str.split(delimiter).str.get(-1)
#     df['Entity2_Normal'] = df['Entity2'].str.split(delimiter).str.get(-1)
#     df['Entity1_Normal'] = df['Entity1_Normal'].apply(util.cleaning)
#     df['Entity2_Normal'] = df['Entity2_Normal'].apply(util.cleaning)
#     # df['Entity1_Normal1'] = df['Entity1_Normal']
#     # df['Entity2_Normal2'] = df['Entity2_Normal'].apply(normal_string)
#     # different_rows = df[df['Entity1_Normal'] != df['Entity1_Normal1']]
#     # print(different_rows)
#     # different_rows = df[df['Entity2_Normal'] != df['Entity2_Normal2']]
#     # print(different_rows)
#     condition = df['Entity1_Normal'] != df['Entity2_Normal']
#     filtered_df = df[condition]
#     filtered_df = filtered_df.drop(columns=['Entity1_Normal', 'Entity2_Normal'])
#     filtered_df.to_csv(output_path, index=False)

def generate_filtered_csv(input_path, trivial_path, output_path):
    df1 = pd.read_csv(input_path)
    df2 = pd.read_csv(trivial_path)
    # Finding rows in df1 that are not in df2
    diff_df = df1[~df1.apply(tuple, 1).isin(df2.apply(tuple, 1))]
    diff_df.to_csv(output_path, index=False)


if __name__ == '__main__':
    # anatomy
    # slight precision difference, ask for confirmation

    # util.create_document("benchmark_anatomy/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    # util.create_document("benchmark_anatomy/result_filter.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    #
    # find_alignment("data/anatomy/mouse-human-suite/component/reference.xml", "benchmark_anatomy/true.csv", True, True)
    #
    # find_alignment("benchmark_anatomy/ALIN.rdf", "benchmark_anatomy/ALIN.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/ALIN.csv",
    #                        "ALIN", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/ALIOn.rdf", "benchmark_anatomy/ALIOn.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/ALIOn.csv",
    #                        "ALIOn", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/AMD.rdf", "benchmark_anatomy/AMD.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/AMD.csv",
    #                        "AMD", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/AtMatch.rdf", "benchmark_anatomy/AtMatch.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/AtMatch.csv",
    #                        "AtMatch", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/IsMatch.rdf", "benchmark_anatomy/IsMatch.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/IsMatch.csv",
    #                        "IsMatch", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/LogMap.rdf", "benchmark_anatomy/LogMap.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/LogMap.csv",
    #                        "LogMap", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/LogMap-Lite.rdf", "benchmark_anatomy/LogMap-Lite.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/LogMap-Lite.csv",
    #                        "LogMap-Lite", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/LogMapBio.rdf", "benchmark_anatomy/LogMapBio.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/LogMapBio.csv",
    #                        "LogMapBio", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/Matcha.rdf", "benchmark_anatomy/Matcha.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/Matcha.csv",
    #                        "Matcha", "benchmark_anatomy/result.csv")
    # find_alignment("benchmark_anatomy/SEBMatcher.rdf", "benchmark_anatomy/SEBMatcher.csv", True, True)
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/SEBMatcher.csv",
    #                        "SEBMatcher", "benchmark_anatomy/result.csv")
    # util.calculate_metrics("benchmark_anatomy/true.csv", "benchmark_anatomy/Agent-OM.csv",
    #                        "Agent-OM", "benchmark_anatomy/result.csv")
    #
    # find_alignment("benchmark_anatomy/trivial.rdf", "benchmark_anatomy/trivial.csv", True, True)
    # generate_filtered_csv("benchmark_anatomy/true.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/true_filter.csv")
    #
    # generate_filtered_csv("benchmark_anatomy/ALIN.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/ALIN_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/ALIN_filter.csv",
    #                        "ALIN", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/ALIOn.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/ALIOn_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/ALIOn_filter.csv",
    #                        "ALIOn", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/AMD.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/AMD_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/AMD_filter.csv",
    #                        "AMD", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/AtMatch.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/AtMatch_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/AtMatch_filter.csv",
    #                        "AtMatch", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/IsMatch.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/IsMatch_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/IsMatch_filter.csv",
    #                        "IsMatch", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/LogMap.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/LogMap_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/LogMap_filter.csv",
    #                        "LogMap", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/LogMap-Lite.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/LogMap-Lite_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/LogMap-Lite_filter.csv",
    #                        "LogMap-Lite", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/LogMapBio.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/LogMapBio_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/LogMapBio_filter.csv",
    #                        "LogMapBio", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/Matcha.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/Matcha_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/Matcha_filter.csv",
    #                        "Matcha", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/SEBMatcher.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/SEBMatcher_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/SEBMatcher_filter.csv",
    #                        "SEBMatcher", "benchmark_anatomy/result_filter.csv")
    # generate_filtered_csv("benchmark_anatomy/Agent-OM.csv", "benchmark_anatomy/trivial.csv", "benchmark_anatomy/Agent-OM_filter.csv")
    # util.calculate_metrics("benchmark_anatomy/true_filter.csv", "benchmark_anatomy/Agent-OM_filter.csv",
    #                        "Agent-OM", "benchmark_anatomy/result_filter.csv")

    # mse
    # Matcha need to remove # after alignment

    # first case
    # ALion has a false subsumption matching
    # util.create_document("benchmark_mse/firstTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    #
    # find_alignment_all("data/mse/MaterialInformationReduced-MatOnto/component/reference.xml",
    #                    "benchmark_mse/firstTestCase/true.csv", False, False)
    #
    # find_alignment_all("benchmark_mse/firstTestCase/ALion.rdf", "benchmark_mse/firstTestCase/ALion.csv", False, False)
    # util.calculate_metrics("benchmark_mse/firstTestCase/true.csv", "benchmark_mse/firstTestCase/ALion.csv",
    #                        "ALion", "benchmark_mse/firstTestCase/result.csv")
    #
    # find_alignment_all("benchmark_mse/firstTestCase/LogMap.rdf", "benchmark_mse/firstTestCase/LogMap.csv", False, False)
    # util.calculate_metrics("benchmark_mse/firstTestCase/true.csv", "benchmark_mse/firstTestCase/LogMap.csv",
    #                        "LogMap", "benchmark_mse/firstTestCase/result.csv")
    #
    # find_alignment_all("benchmark_mse/firstTestCase/LogMapLight.rdf", "benchmark_mse/firstTestCase/LogMapLight.csv",
    #                    False, False)
    # util.calculate_metrics("benchmark_mse/firstTestCase/true.csv", "benchmark_mse/firstTestCase/LogMapLight.csv",
    #                        "LogMapLight", "benchmark_mse/firstTestCase/result.csv")
    #
    # find_alignment_all("benchmark_mse/firstTestCase/Matcha.rdf", "benchmark_mse/firstTestCase/Matcha.csv", False, False)
    # util.calculate_metrics("benchmark_mse/firstTestCase/true.csv", "benchmark_mse/firstTestCase/Matcha.csv",
    #                        "Matcha", "benchmark_mse/firstTestCase/result.csv")
    #
    # util.calculate_metrics("benchmark_mse/firstTestCase/true.csv", "benchmark_mse/firstTestCase/Agent-OM.csv",
    #                        "Agent-OM", "benchmark_mse/firstTestCase/result.csv")

    # second case
    util.create_document("benchmark_mse/secondTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("benchmark_mse/secondTestCase/ALion.rdf", "benchmark_mse/secondTestCase/ALion.csv", False, False)
    util.calculate_metrics("benchmark_mse/secondTestCase/true.csv", "benchmark_mse/secondTestCase/ALion.csv",
                           "ALion", "benchmark_mse/secondTestCase/result.csv")

    find_alignment("benchmark_mse/secondTestCase/LogMap.rdf", "benchmark_mse/secondTestCase/LogMap.csv", False, False)
    util.calculate_metrics("benchmark_mse/secondTestCase/true.csv", "benchmark_mse/secondTestCase/LogMap.csv",
                           "LogMap", "benchmark_mse/secondTestCase/result.csv")

    find_alignment("benchmark_mse/secondTestCase/LogMapLight.rdf", "benchmark_mse/secondTestCase/LogMapLight.csv", False, False)
    util.calculate_metrics("benchmark_mse/secondTestCase/true.csv", "benchmark_mse/secondTestCase/LogMapLight.csv",
                           "LogMapLight", "benchmark_mse/secondTestCase/result.csv")

    find_alignment("benchmark_mse/secondTestCase/Matcha.rdf", "benchmark_mse/secondTestCase/Matcha.csv", False, False)
    util.calculate_metrics("benchmark_mse/secondTestCase/true.csv", "benchmark_mse/secondTestCase/Matcha.csv",
                           "Matcha", "benchmark_mse/secondTestCase/result.csv")

    util.calculate_metrics("benchmark_mse/secondTestCase/true.csv", "benchmark_mse/secondTestCase/Agent-OM.csv",
                           "Agent-OM", "benchmark_mse/secondTestCase/result.csv")

    # third case
    # util.create_document("benchmark_mse/thirdTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    #
    # find_alignment("benchmark_mse/thirdTestCase/ALion.rdf", "benchmark_mse/thirdTestCase/ALion.csv", False, True)
    # util.calculate_metrics("benchmark_mse/thirdTestCase/true.csv", "benchmark_mse/thirdTestCase/ALion.csv",
    #                        "ALion", "benchmark_mse/thirdTestCase/result.csv")
    #
    # find_alignment("benchmark_mse/thirdTestCase/LogMap.rdf", "benchmark_mse/thirdTestCase/LogMap.csv", False, True)
    # util.calculate_metrics("benchmark_mse/thirdTestCase/true.csv", "benchmark_mse/thirdTestCase/LogMap.csv",
    #                        "LogMap", "benchmark_mse/thirdTestCase/result.csv")
    #
    # find_alignment("benchmark_mse/thirdTestCase/LogMapLight.rdf", "benchmark_mse/thirdTestCase/LogMapLight.csv", False, True)
    # util.calculate_metrics("benchmark_mse/thirdTestCase/true.csv", "benchmark_mse/thirdTestCase/LogMapLight.csv",
    #                        "LogMapLight", "benchmark_mse/thirdTestCase/result.csv")
    #
    # find_alignment("benchmark_mse/thirdTestCase/Matcha.rdf", "benchmark_mse/thirdTestCase/Matcha.csv", False, True)
    # util.calculate_metrics("benchmark_mse/thirdTestCase/true.csv", "benchmark_mse/thirdTestCase/Matcha.csv",
    #                        "Matcha", "benchmark_mse/thirdTestCase/result.csv")
    #
    # util.calculate_metrics("benchmark_mse/thirdTestCase/true.csv", "benchmark_mse/thirdTestCase/Agent-OM.csv",
    #                        "Agent-OM", "benchmark_mse/thirdTestCase/result.csv")
