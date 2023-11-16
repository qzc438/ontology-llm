import util
import rdflib
import csv
import pandas as pd

alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')

o1_path = "data/anatomy/mouse-human-suite/component/source.xml"
o2_path = "data/anatomy/mouse-human-suite/component/target.xml"

is_code = True
o1 = rdflib.Graph().parse(o1_path, format="xml")
o2 = rdflib.Graph().parse(o2_path, format="xml")
o1_prefix = "source"
o2_prefix = "target"


def get_entity_label(entity, ontology):
    entity_label = ""
    for s, p, o in ontology.triples((entity, rdflib.RDFS.label, None)):
        entity_label = str(o)
    return entity_label


def get_entity_name(entity, ontology):
    if is_code:
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
            e1_uri = align.value(s, alignEntity1, None)
            e2_uri = align.value(s, alignEntity2, None)
            e1_name = get_entity_name(e1_uri, o1)
            e2_name = get_entity_name(e2_uri, o2)
            e1_prefix_name = util.name_to_prefix_name(e1_name, o1_prefix)
            e2_prefix_name = util.name_to_prefix_name(e2_name, o2_prefix)
            list_pair = [e1_prefix_name, e2_prefix_name]
            writer.writerow(list_pair)


def generate_filtered_csv(input_path, output_path):
    df = pd.read_csv(input_path)
    delimiter = ':'
    df['Entity1_Normal'] = df['Entity1'].str.split(delimiter).str.get(-1)
    df['Entity2_Normal'] = df['Entity2'].str.split(delimiter).str.get(-1)
    df['Entity1_Normal'] = df['Entity1_Normal'].apply(util.cleaning)
    df['Entity2_Normal'] = df['Entity2_Normal'].apply(util.cleaning)
    condition = df['Entity1_Normal'] != df['Entity2_Normal']
    filtered_df = df[condition]
    filtered_df = filtered_df.drop(columns=['Entity1_Normal', 'Entity2_Normal'])
    filtered_df.to_csv(output_path, index=False)


if __name__ == '__main__':

    util.create_document("anatomy_benchmark/result.csv", header=['Name', 'Precision', 'Recall', 'F1'])
    util.create_document("anatomy_benchmark/result_filter.csv", header=['Name', 'Precision', 'Recall', 'F1'])

    find_alignment("data/anatomy/mouse-human-suite/component/reference.xml", "anatomy_benchmark/true.csv")
    generate_filtered_csv("anatomy_benchmark/true.csv", "anatomy_benchmark/true_filter.csv")

    find_alignment("anatomy_benchmark/ALIN.rdf", "anatomy_benchmark/ALIN.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/ALIN.csv",
                           "ALIN", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/ALIN.csv", "anatomy_benchmark/ALIN_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/ALIN_filter.csv",
                           "ALIN", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/ALIOn.rdf", "anatomy_benchmark/ALIOn.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/ALIOn.csv",
                           "ALIOn", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/ALIOn.csv", "anatomy_benchmark/ALIOn_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/ALIOn_filter.csv",
                           "ALIOn", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/AMD.rdf", "anatomy_benchmark/AMD.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/AMD.csv",
                           "AMD", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/AMD.csv", "anatomy_benchmark/AMD_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/AMD_filter.csv",
                           "AMD", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/AtMatch.rdf", "anatomy_benchmark/AtMatch.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/AtMatch.csv",
                           "AtMatch", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/AtMatch.csv", "anatomy_benchmark/AtMatch_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/AtMatch_filter.csv",
                           "AtMatch", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/IsMatch.rdf", "anatomy_benchmark/IsMatch.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/IsMatch.csv",
                           "IsMatch", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/IsMatch.csv", "anatomy_benchmark/IsMatch_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/IsMatch_filter.csv",
                           "IsMatch", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/LogMap.rdf", "anatomy_benchmark/LogMap.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/LogMap.csv",
                           "LogMap", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/LogMap.csv", "anatomy_benchmark/LogMap_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/LogMap_filter.csv",
                           "LogMap", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/LogMap-Lite.rdf", "anatomy_benchmark/LogMap-Lite.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/LogMap-Lite.csv",
                           "LogMap-Lite", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/LogMap-Lite.csv", "anatomy_benchmark/LogMap-Lite_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/LogMap-Lite_filter.csv",
                           "LogMap-Lite", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/LogMapBio.rdf", "anatomy_benchmark/LogMapBio.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/LogMapBio.csv",
                           "LogMapBio", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/LogMapBio.csv", "anatomy_benchmark/LogMapBio_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/LogMapBio_filter.csv",
                           "LogMapBio", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/Matcha.rdf", "anatomy_benchmark/Matcha.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/Matcha.csv",
                           "Matcha", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/Matcha.csv", "anatomy_benchmark/Matcha_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/Matcha_filter.csv",
                           "Matcha", "anatomy_benchmark/result_filter.csv")

    find_alignment("anatomy_benchmark/SEBMatcher.rdf", "anatomy_benchmark/SEBMatcher.csv")
    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/SEBMatcher.csv",
                           "SEBMatcher", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/SEBMatcher.csv", "anatomy_benchmark/SEBMatcher_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/SEBMatcher_filter.csv",
                           "SEBMatcher", "anatomy_benchmark/result_filter.csv")

    util.calculate_metrics("anatomy_benchmark/true.csv", "anatomy_benchmark/Agent-OM.csv",
                           "Agent-OM", "anatomy_benchmark/result.csv")
    generate_filtered_csv("anatomy_benchmark/Agent-OM.csv", "anatomy_benchmark/Agent-OM_filter.csv")
    util.calculate_metrics("anatomy_benchmark/true_filter.csv", "anatomy_benchmark/Agent-OM_filter.csv",
                           "Agent-OM", "anatomy_benchmark/result_filter.csv")
