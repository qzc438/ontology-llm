import util
import rdflib
import csv
import pandas as pd

alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#Cell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity2')
alignRelation = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#relation')

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


def find_alignment(align_path, true_path):
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
                # e1_name = get_entity_name(e1_uri, o1, o1_is_code)
                # e2_name = get_entity_name(e2_uri, o2, o2_is_code)
                # e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
                # e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
                list_pair = [e1_uri, e2_uri]
                writer.writerow(list_pair)
    # Find duplicates
    df = pd.read_csv(true_path)
    duplicates = df.duplicated().sum()
    print(f"Number of duplicate rows in {align_path}: {duplicates}")
    df_no_duplicates = df.drop_duplicates(keep='first')
    df_no_duplicates.to_csv(true_path, index=False)


def find_alignment_all(align_path, true_path):
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
            # e1_name = get_entity_name(e1_uri, o1, o1_is_code)
            # e2_name = get_entity_name(e2_uri, o2, o2_is_code)
            # e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
            # e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
            list_pair = [e1_uri, e2_uri]
            writer.writerow(list_pair)
    # Find duplicates
    df = pd.read_csv(true_path)
    duplicates = df.duplicated().sum()
    print(f"Number of duplicate rows in {align_path}: {duplicates}")
    df_no_duplicates = df.drop_duplicates(keep='first')
    df_no_duplicates.to_csv(true_path, index=False)


def normal_string(original_string):
    return original_string.replace('_', ' ').lower()


def generate_filtered_csv(input_path, trivial_path, output_path):
    df1 = pd.read_csv(input_path)
    df2 = pd.read_csv(trivial_path)
    # Finding rows in df1 that are not in df2
    diff_df = df1[~df1.apply(tuple, 1).isin(df2.apply(tuple, 1))]
    diff_df.to_csv(output_path, index=False)


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


if __name__ == '__main__':
    # anatomy, please remember to remove mappings between oboinowl name spaced concepts, totally 8
    # source: DbXref, target: DbXref
    # source: Definition, target: Definition
    # source: ObsoleteClass, target: ObsoleteClass
    # source: Subset, target: Subset
    # source: Synonym, target: Synonym
    # source: SynonymType, target: SynonymType
    # source: Part of, target: part of
    # source: ObsoleteProperty, target: ObsoleteProperty

    # anatomy track
    o1_path = "data/anatomy/mouse-human-suite/component/source.xml"
    o2_path = "data/anatomy/mouse-human-suite/component/target.xml"
    o1 = rdflib.Graph().parse(o1_path, format="xml")
    o2 = rdflib.Graph().parse(o2_path, format="xml")

    # 2022 results
    util.create_document("benchmark_2022/anatomy/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    util.create_document("benchmark_2022/anatomy/result_filter.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/anatomy/mouse-human-suite/component/reference.xml", "benchmark_2022/anatomy/true.csv")

    find_alignment("benchmark_2022/anatomy/ALIN.rdf", "benchmark_2022/anatomy/ALIN.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/ALIN.csv",
                                     "benchmark_2022/anatomy/result.csv", "ALIN")
    find_alignment("benchmark_2022/anatomy/ALIOn.rdf", "benchmark_2022/anatomy/ALIOn.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/ALIOn.csv",
                                     "benchmark_2022/anatomy/result.csv", "ALIOn")
    find_alignment("benchmark_2022/anatomy/AMD.rdf", "benchmark_2022/anatomy/AMD.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/AMD.csv",
                                     "benchmark_2022/anatomy/result.csv", "AMD")
    find_alignment("benchmark_2022/anatomy/AtMatch.rdf", "benchmark_2022/anatomy/AtMatch.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/AtMatch.csv",
                                     "benchmark_2022/anatomy/result.csv", "ATMatcher")
    find_alignment("benchmark_2022/anatomy/IsMatch.rdf", "benchmark_2022/anatomy/IsMatch.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/IsMatch.csv",
                                     "benchmark_2022/anatomy/result.csv", "LSMatch")
    find_alignment("benchmark_2022/anatomy/LogMap.rdf", "benchmark_2022/anatomy/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/LogMap.csv",
                                     "benchmark_2022/anatomy/result.csv", "LogMap")
    find_alignment("benchmark_2022/anatomy/LogMap-Lite.rdf", "benchmark_2022/anatomy/LogMap-Lite.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/LogMap-Lite.csv",
                                     "benchmark_2022/anatomy/result.csv", "LogMapLt")
    find_alignment("benchmark_2022/anatomy/LogMapBio.rdf", "benchmark_2022/anatomy/LogMapBio.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/LogMapBio.csv",
                                     "benchmark_2022/anatomy/result.csv", "LogMapBio")
    find_alignment("benchmark_2022/anatomy/Matcha.rdf", "benchmark_2022/anatomy/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/Matcha.csv",
                                     "benchmark_2022/anatomy/result.csv", "Matcha")
    find_alignment("benchmark_2022/anatomy/SEBMatcher.rdf", "benchmark_2022/anatomy/SEBMatcher.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/SEBMatcher.csv",
                                     "benchmark_2022/anatomy/result.csv", "SEBMatcher")

    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true.csv",
                                     "alignment/anatomy/mouse-human-suite/component/predict.csv",
                                     "benchmark_2022/anatomy/result.csv", "Agent-OM")

    find_alignment("benchmark_2022/anatomy/trivial.rdf", "benchmark_2022/anatomy/trivial.csv")
    generate_filtered_csv("benchmark_2022/anatomy/true.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/true_filter.csv")

    generate_filtered_csv("benchmark_2022/anatomy/ALIN.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/ALIN_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv", "benchmark_2022/anatomy/ALIN_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "ALIN")
    generate_filtered_csv("benchmark_2022/anatomy/ALIOn.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/ALIOn_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/ALIOn_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "ALIOn")
    generate_filtered_csv("benchmark_2022/anatomy/AMD.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/AMD_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv", "benchmark_2022/anatomy/AMD_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "AMD")
    generate_filtered_csv("benchmark_2022/anatomy/AtMatch.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/AtMatch_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/AtMatch_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "ATMatcher")
    generate_filtered_csv("benchmark_2022/anatomy/IsMatch.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/IsMatch_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/IsMatch_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "LSMatch")
    generate_filtered_csv("benchmark_2022/anatomy/LogMap.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/LogMap_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/LogMap_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "LogMap")
    generate_filtered_csv("benchmark_2022/anatomy/LogMap-Lite.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/LogMap-Lite_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/LogMap-Lite_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "LogMapLt")
    generate_filtered_csv("benchmark_2022/anatomy/LogMapBio.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/LogMapBio_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/LogMapBio_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "LogMapBio")
    generate_filtered_csv("benchmark_2022/anatomy/Matcha.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/Matcha_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/Matcha_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "Matcha")
    generate_filtered_csv("benchmark_2022/anatomy/SEBMatcher.csv", "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/SEBMatcher_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/SEBMatcher_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "SEBMatcher")
    generate_filtered_csv("alignment/anatomy/mouse-human-suite/component/predict.csv",
                          "benchmark_2022/anatomy/trivial.csv",
                          "benchmark_2022/anatomy/Agent-OM_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2022/anatomy/true_filter.csv",
                                     "benchmark_2022/anatomy/Agent-OM_filter.csv",
                                     "benchmark_2022/anatomy/result_filter.csv", "Agent-OM")

    # 2023 results
    util.create_document("benchmark_2023/anatomy/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    util.create_document("benchmark_2023/anatomy/result_filter.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/anatomy/mouse-human-suite/component/reference.xml", "benchmark_2023/anatomy/true.csv")

    find_alignment("benchmark_2023/anatomy/ALIN.rdf", "benchmark_2023/anatomy/ALIN.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/ALIN.csv",
                                     "benchmark_2023/anatomy/result.csv", "ALIN")
    find_alignment("benchmark_2023/anatomy/AMD.rdf", "benchmark_2023/anatomy/AMD.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/AMD.csv",
                                     "benchmark_2023/anatomy/result.csv", "AMD")
    find_alignment("benchmark_2023/anatomy/LogMap.rdf", "benchmark_2023/anatomy/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/LogMap.csv",
                                     "benchmark_2023/anatomy/result.csv", "LogMap")
    find_alignment("benchmark_2023/anatomy/LogMapBio.rdf", "benchmark_2023/anatomy/LogMapBio.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/LogMapBio.csv",
                                     "benchmark_2023/anatomy/result.csv", "LogMapBio")
    find_alignment("benchmark_2023/anatomy/LogMapLite.rdf", "benchmark_2023/anatomy/LogMapLite.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/LogMapLite.csv",
                                     "benchmark_2023/anatomy/result.csv", "LogMapLt")
    find_alignment("benchmark_2023/anatomy/LSMatch.rdf", "benchmark_2023/anatomy/LSMatch.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/LSMatch.csv",
                                     "benchmark_2023/anatomy/result.csv", "LSMatch")
    find_alignment("benchmark_2023/anatomy/Matcha.rdf", "benchmark_2023/anatomy/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/Matcha.csv",
                                     "benchmark_2023/anatomy/result.csv", "Matcha")
    find_alignment("benchmark_2023/anatomy/OLaLa.rdf", "benchmark_2023/anatomy/OLaLa.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/OLaLa.csv",
                                     "benchmark_2023/anatomy/result.csv", "OLala")
    find_alignment("benchmark_2023/anatomy/SORBETMatch.rdf", "benchmark_2023/anatomy/SORBETMatch.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/SORBETMatch.csv",
                                     "benchmark_2023/anatomy/result.csv", "SORBETMatch", )

    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true.csv",
                                     "alignment/anatomy/mouse-human-suite/component/predict.csv",
                                     "benchmark_2023/anatomy/result.csv", "Agent-OM", )

    find_alignment("benchmark_2023/anatomy/trivial.rdf", "benchmark_2023/anatomy/trivial.csv")
    generate_filtered_csv("benchmark_2023/anatomy/true.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/true_filter.csv")

    generate_filtered_csv("benchmark_2023/anatomy/ALIN.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/ALIN_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv", "benchmark_2023/anatomy/ALIN_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "ALIN")
    generate_filtered_csv("benchmark_2023/anatomy/AMD.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/AMD_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv", "benchmark_2023/anatomy/AMD_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "AMD")
    generate_filtered_csv("benchmark_2023/anatomy/LogMap.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/LogMap_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/LogMap_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "LogMap")
    generate_filtered_csv("benchmark_2023/anatomy/LogMapBio.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/LogMapBio_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/LogMapBio_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "LogMapBio")
    generate_filtered_csv("benchmark_2023/anatomy/LogMapLite.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/LogMapLite_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/LogMapLite_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "LogMapLt")
    generate_filtered_csv("benchmark_2023/anatomy/LSMatch.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/LSMatch_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/LSMatch_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "LSMatch")
    generate_filtered_csv("benchmark_2023/anatomy/Matcha.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/Matcha_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/Matcha_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "Matcha")
    generate_filtered_csv("benchmark_2023/anatomy/OLaLa.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/OLaLa_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/OLaLa_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "OLaLa")
    generate_filtered_csv("benchmark_2023/anatomy/SORBETMatch.csv", "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/SORBETMatch_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/SORBETMatch_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "SORBETMatch")

    generate_filtered_csv("alignment/anatomy/mouse-human-suite/component/predict.csv",
                          "benchmark_2023/anatomy/trivial.csv",
                          "benchmark_2023/anatomy/Agent-OM_filter.csv")
    util.calculate_benchmark_metrics("benchmark_2023/anatomy/true_filter.csv",
                                     "benchmark_2023/anatomy/Agent-OM_filter.csv",
                                     "benchmark_2023/anatomy/result_filter.csv", "Agent-OM")

    # mse

    # mse track first case
    o1_path = "data/mse/MaterialInformationReduced-MatOnto/component/source.xml"
    o2_path = "data/mse/MaterialInformationReduced-MatOnto/component/target.xml"
    o1 = rdflib.Graph().parse(o1_path, format="xml")
    o2 = rdflib.Graph().parse(o2_path, format="xml")

    # 2022 results
    util.create_document("benchmark_2022/mse/firstTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment_all("data/mse/MaterialInformationReduced-MatOnto/component/reference.xml",
                       "benchmark_2022/mse/firstTestCase/true.csv")

    find_alignment_all("benchmark_2022/mse/firstTestCase/ALion.rdf", "benchmark_2022/mse/firstTestCase/ALion.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/firstTestCase/true.csv",
                                     "benchmark_2022/mse/firstTestCase/ALion.csv",
                                     "benchmark_2022/mse/firstTestCase/result.csv", "ALIOn")
    # df1 = pd.read_csv("benchmark_2022/mse/firstTestCase/ALion.csv")
    # df2 = pd.read_csv("benchmark_2022/mse/firstTestCase/true.csv")
    # merged_df = pd.merge(df1, df2, on=['Entity1', 'Entity2'])
    # print("ALion-2022", merged_df)
    find_alignment_all("benchmark_2022/mse/firstTestCase/LogMap.rdf", "benchmark_2022/mse/firstTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/firstTestCase/true.csv",
                                     "benchmark_2022/mse/firstTestCase/LogMap.csv",
                                     "benchmark_2022/mse/firstTestCase/result.csv", "LogMap")
    find_alignment_all("benchmark_2022/mse/firstTestCase/LogMapLight.rdf",
                       "benchmark_2022/mse/firstTestCase/LogMapLight.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/firstTestCase/true.csv",
                                     "benchmark_2022/mse/firstTestCase/LogMapLight.csv",
                                     "benchmark_2022/mse/firstTestCase/result.csv", "LogMapLt")
    find_alignment_all("benchmark_2022/mse/firstTestCase/Matcha.rdf", "benchmark_2022/mse/firstTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/firstTestCase/true.csv",
                                     "benchmark_2022/mse/firstTestCase/Matcha.csv",
                                     "benchmark_2022/mse/firstTestCase/result.csv", "Matcha")

    util.calculate_benchmark_metrics("benchmark_2022/mse/firstTestCase/true.csv",
                                     "alignment/mse/MaterialInformationReduced-MatOnto/component/predict.csv",
                                     "benchmark_2022/mse/firstTestCase/result.csv", "Agent-OM")
    # df1 = pd.read_csv("alignment/mse/MaterialInformationReduced-MatOnto/component/predict.csv")
    # df2 = pd.read_csv("benchmark_2022/mse/firstTestCase/true.csv")
    # merged_df = pd.merge(df1, df2, on=['Entity1', 'Entity2'])
    # print("Agent-OM-2022", merged_df)

    # 2023 results
    util.create_document("benchmark_2023/mse/firstTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment_all("data/mse/MaterialInformationReduced-MatOnto/component/reference.xml",
                       "benchmark_2023/mse/firstTestCase/true.csv")

    find_alignment_all("benchmark_2023/mse/firstTestCase/LogMap.rdf", "benchmark_2023/mse/firstTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/firstTestCase/true.csv",
                                     "benchmark_2023/mse/firstTestCase/LogMap.csv",
                                     "benchmark_2023/mse/firstTestCase/result.csv", "LogMap")
    find_alignment_all("benchmark_2023/mse/firstTestCase/LogMapLite.rdf",
                       "benchmark_2023/mse/firstTestCase/LogMapLite.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/firstTestCase/true.csv",
                                     "benchmark_2023/mse/firstTestCase/LogMapLite.csv",
                                     "benchmark_2023/mse/firstTestCase/result.csv", "LogMapLt")
    # Matcha has a 1 false subsumption matching:  source:ConcentrationOfSolvent and target:Concentration
    find_alignment_all("benchmark_2023/mse/firstTestCase/Matcha.rdf", "benchmark_2023/mse/firstTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/firstTestCase/true.csv",
                                     "benchmark_2023/mse/firstTestCase/Matcha.csv",
                                     "benchmark_2023/mse/firstTestCase/result.csv", "Matcha")
    # df1 = pd.read_csv("benchmark_2023/mse/firstTestCase/Matcha.csv")
    # df2 = pd.read_csv("benchmark_2023/mse/firstTestCase/true.csv")
    # merged_df = pd.merge(df1, df2, on=['Entity1', 'Entity2'])
    # print("Matcha-2023", merged_df)

    util.calculate_benchmark_metrics("benchmark_2023/mse/firstTestCase/true.csv",
                                     "alignment/mse/MaterialInformationReduced-MatOnto/component/predict.csv",
                                     "benchmark_2023/mse/firstTestCase/result.csv", "Agent-OM")
    # df1 = pd.read_csv("alignment/mse/MaterialInformationReduced-MatOnto/component/predict.csv")
    # df2 = pd.read_csv("benchmark_2023/mse/firstTestCase/true.csv")
    # merged_df = pd.merge(df1, df2, on=['Entity1', 'Entity2'])
    # print("Agent-OM-2023", merged_df)

    # mse track second case
    o1_path = "data/mse/MaterialInformation-MatOnto/component/source.xml"
    o2_path = "data/mse/MaterialInformation-MatOnto/component/target.xml"
    o1 = rdflib.Graph().parse(o1_path, format="xml")
    o2 = rdflib.Graph().parse(o2_path, format="xml")

    # 2022 results
    util.create_document("benchmark_2022/mse/secondTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/mse/MaterialInformation-MatOnto/component/reference.xml",
                   "benchmark_2022/mse/secondTestCase/true.csv")

    find_alignment("benchmark_2022/mse/secondTestCase/ALion.rdf", "benchmark_2022/mse/secondTestCase/ALion.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/secondTestCase/true.csv",
                                     "benchmark_2022/mse/secondTestCase/ALion.csv",
                                     "benchmark_2022/mse/secondTestCase/result.csv", "ALIOn")
    find_alignment("benchmark_2022/mse/secondTestCase/LogMap.rdf", "benchmark_2022/mse/secondTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/secondTestCase/true.csv",
                                     "benchmark_2022/mse/secondTestCase/LogMap.csv",
                                     "benchmark_2022/mse/secondTestCase/result.csv", "LogMap")
    find_alignment("benchmark_2022/mse/secondTestCase/LogMapLight.rdf",
                   "benchmark_2022/mse/secondTestCase/LogMapLight.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/secondTestCase/true.csv",
                                     "benchmark_2022/mse/secondTestCase/LogMapLight.csv",
                                     "benchmark_2022/mse/secondTestCase/result.csv", "LogMapLt")
    find_alignment("benchmark_2022/mse/secondTestCase/Matcha.rdf", "benchmark_2022/mse/secondTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/secondTestCase/true.csv",
                                     "benchmark_2022/mse/secondTestCase/Matcha.csv",
                                     "benchmark_2022/mse/secondTestCase/result.csv", "Matcha")
    util.calculate_benchmark_metrics("benchmark_2022/mse/secondTestCase/true.csv",
                                     "alignment/mse/MaterialInformation-MatOnto/component/predict.csv",
                                     "benchmark_2022/mse/secondTestCase/result.csv", "Agent-OM")

    # 2023 results
    util.create_document("benchmark_2023/mse/secondTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/mse/MaterialInformation-MatOnto/component/reference.xml",
                   "benchmark_2023/mse/secondTestCase/true.csv")

    find_alignment("benchmark_2023/mse/secondTestCase/LogMap.rdf", "benchmark_2023/mse/secondTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/secondTestCase/true.csv",
                                     "benchmark_2023/mse/secondTestCase/LogMap.csv",
                                     "benchmark_2023/mse/secondTestCase/result.csv", "LogMap")
    find_alignment("benchmark_2023/mse/secondTestCase/LogMapLite.rdf",
                   "benchmark_2023/mse/secondTestCase/LogMapLite.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/secondTestCase/true.csv",
                                     "benchmark_2023/mse/secondTestCase/LogMapLite.csv",
                                     "benchmark_2023/mse/secondTestCase/result.csv", "LogMapLt")
    find_alignment("benchmark_2023/mse/secondTestCase/Matcha.rdf", "benchmark_2023/mse/secondTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/secondTestCase/true.csv",
                                     "benchmark_2023/mse/secondTestCase/Matcha.csv",
                                     "benchmark_2023/mse/secondTestCase/result.csv", "Matcha")
    util.calculate_benchmark_metrics("benchmark_2023/mse/secondTestCase/true.csv",
                                     "alignment/mse/MaterialInformation-MatOnto/component/predict.csv",
                                     "benchmark_2023/mse/secondTestCase/result.csv", "Agent-OM")

    # mse track third case
    o1_path = "data/mse/MaterialInformation-EMMO/component/source.xml"
    o2_path = "data/mse/MaterialInformation-EMMO/component/target.xml"
    o1 = rdflib.Graph().parse(o1_path, format="xml")
    o2 = rdflib.Graph().parse(o2_path, format="xml")

    # 2022 results
    util.create_document("benchmark_2022/mse/thirdTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/mse/MaterialInformation-EMMO/component/reference.xml",
                   "benchmark_2022/mse/thirdTestCase/true.csv")

    find_alignment("benchmark_2022/mse/thirdTestCase/ALion.rdf", "benchmark_2022/mse/thirdTestCase/ALion.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/thirdTestCase/true.csv",
                                     "benchmark_2022/mse/thirdTestCase/ALion.csv",
                                     "benchmark_2022/mse/thirdTestCase/result.csv", "ALIOn")
    find_alignment("benchmark_2022/mse/thirdTestCase/LogMap.rdf", "benchmark_2022/mse/thirdTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/thirdTestCase/true.csv",
                                     "benchmark_2022/mse/thirdTestCase/LogMap.csv",
                                     "benchmark_2022/mse/thirdTestCase/result.csv", "LogMap")
    find_alignment("benchmark_2022/mse/thirdTestCase/LogMapLight.rdf",
                   "benchmark_2022/mse/thirdTestCase/LogMapLight.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/thirdTestCase/true.csv",
                                     "benchmark_2022/mse/thirdTestCase/LogMapLight.csv",
                                     "benchmark_2022/mse/thirdTestCase/result.csv", "LogMapLt")
    find_alignment("benchmark_2022/mse/thirdTestCase/Matcha.rdf", "benchmark_2022/mse/thirdTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2022/mse/thirdTestCase/true.csv",
                                     "benchmark_2022/mse/thirdTestCase/Matcha.csv",
                                     "benchmark_2022/mse/thirdTestCase/result.csv", "Matcha")
    util.calculate_benchmark_metrics("benchmark_2022/mse/thirdTestCase/true.csv",
                                     "alignment/mse/MaterialInformation-EMMO/component/predict.csv",
                                     "benchmark_2022/mse/thirdTestCase/result.csv", "Agent-OM")

    # 2023 results
    util.create_document("benchmark_2023/mse/thirdTestCase/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/mse/MaterialInformation-EMMO/component/reference.xml",
                   "benchmark_2023/mse/thirdTestCase/true.csv")

    find_alignment("benchmark_2023/mse/thirdTestCase/LogMap.rdf", "benchmark_2023/mse/thirdTestCase/LogMap.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/thirdTestCase/true.csv",
                                     "benchmark_2023/mse/thirdTestCase/LogMap.csv",
                                     "benchmark_2023/mse/thirdTestCase/result.csv", "LogMap")
    find_alignment("benchmark_2023/mse/thirdTestCase/LogMapLite.rdf", "benchmark_2023/mse/thirdTestCase/LogMapLite.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/thirdTestCase/true.csv",
                                     "benchmark_2023/mse/thirdTestCase/LogMapLite.csv",
                                     "benchmark_2023/mse/thirdTestCase/result.csv", "LogMapLt")
    find_alignment("benchmark_2023/mse/thirdTestCase/Matcha.rdf", "benchmark_2023/mse/thirdTestCase/Matcha.csv")
    util.calculate_benchmark_metrics("benchmark_2023/mse/thirdTestCase/true.csv",
                                     "benchmark_2023/mse/thirdTestCase/Matcha.csv",
                                     "benchmark_2023/mse/thirdTestCase/result.csv", "Matcha")
    util.calculate_benchmark_metrics("benchmark_2023/mse/thirdTestCase/true.csv",
                                     "alignment/mse/MaterialInformation-EMMO/component/predict.csv",
                                     "benchmark_2023/mse/thirdTestCase/result.csv", "Agent-OM")
