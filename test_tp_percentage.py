import rdflib
import util
import csv
import pandas as pd
import matplotlib.pyplot as plt
import os

alignment = "biodiv/envo-sweet/component/"
o1_is_code = True
o2_is_code = False

# alignment = "biodiv/fish-zooplankton/component/"
# alignment = "biodiv/macroalgae-macrozoobenthos/component/"
# alignment = "biodiv/taxrefldBacteria-ncbitaxonBacteria/component/"
# alignment = "biodiv/taxrefldChromista-ncbitaxonChromista/component/"
# alignment = "biodiv/taxrefldProtozoa-ncbitaxonProtozoa/component/"
# alignment = "biodiv/taxrefldFungi-ncbitaxonFungi/component/" # large
# alignment = "biodiv/taxrefldPlantae-ncbitaxonPlantae/component/" # large
# alignment = "biodiv/taxrefldAnimalia-ncbitaxonAnimalia/component/" # very large
# o1_is_code = True
# o2_is_code = True

# alignment = "bio-ml/ncit-doid/component/"
# alignment = "bio-ml/omim-ordo/component/"
# alignment = "bio-ml/snomed-fma.body/component/"
# alignment = "bio-ml/snomed-ncit.neoplas/component/"
# alignment = "bio-ml/snomed-ncit.pharm/component/"
# o1_is_code = True
# o2_is_code = True

alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#Cell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#entity2')
alignRelation = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignment#relation')

def find_file(data_folder, base_name, extensions=("xml", "rdf", "owl")):
    for ext in extensions:
        path = os.path.join(data_folder, f"{base_name}.{ext}")
        if os.path.exists(path):
            return path
    return None

data_folder = "data/" + alignment
o1_path = find_file(data_folder, "source")
o2_path = find_file(data_folder, "target")
align_path = find_file(data_folder, "reference")

# load ontology
o1 = rdflib.Graph().parse(o1_path)
o2 = rdflib.Graph().parse(o2_path)

def find_reference(align_path, true_path):
    # load alignment file
    align = rdflib.Graph().parse(align_path)

    # create true csv with header
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
                writer.writerow([e1_name, e2_name])

    # read, sort, and rewrite preserving header
    with open(true_path, "r") as f:
        reader = csv.reader(f)
        data = list(reader)

    if data:
        header, rows = data[0], data[1:]
        sorted_rows = sorted(rows, key=lambda x: x[0])

        with open(true_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(sorted_rows)


def find_all_entities():
    # here entity is uri
    e1_list_class = []
    e2_list_class = []
    for x in o1.subjects(rdflib.RDF.type, None):
        if (x, rdflib.RDF.type, rdflib.OWL.Class) in o1 or (x, rdflib.RDF.type, rdflib.SKOS.Concept) in o1:
            if x and ("#" in x or "/" in x) and x != rdflib.OWL.Thing:
                e1_list_class.append(x)
    for y in o2.subjects(rdflib.RDF.type, None):
        if (y, rdflib.RDF.type, rdflib.OWL.Class) in o2 or (y, rdflib.RDF.type, rdflib.SKOS.Concept) in o2:
            if y and ("#" in y or "/" in y) and y != rdflib.OWL.Thing:
                e2_list_class.append(y)
    e1_list_property = []
    e2_list_property = []
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x and ("#" in x or "/" in x):
            e1_list_property.append(x)
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x and ("#" in x or "/" in x):
            e1_list_property.append(x)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y and ("#" in y or "/" in y):
            e2_list_property.append(y)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y and ("#" in y or "/" in y):
            e2_list_property.append(y)
    # sort each list
    e1_list_class.sort()
    e2_list_class.sort()
    e1_list_property.sort()
    e2_list_property.sort()
    # check each list
    print("e1_list_class:", len(e1_list_class))
    print("e2_list_class:", len(e2_list_class))
    print("e1_list_property:", len(e1_list_property))
    print("e2_list_property:", len(e2_list_property))
    print()
    return e1_list_class, e2_list_class, e1_list_property, e2_list_property


def get_entity_label(entity, ontology):
    entity_label = ""
    results_rdfs = set(ontology.triples((rdflib.URIRef(entity), rdflib.RDFS.label, None)))
    results_skos = set(ontology.triples((rdflib.URIRef(entity), rdflib.SKOS.prefLabel, None)))
    combined_results = results_rdfs.union(results_skos)
    for s, p, o in combined_results:
        entity_label = str(o)
    return entity_label


def get_entity_name(entity, ontology, ontology_is_code):
    if ontology_is_code:
        entity_name = get_entity_label(entity, ontology) or util.uri_to_name(entity)
    else:
        entity_name = util.uri_to_name(entity)
    return entity_name


def plot_tp_fp_pie(true_csv: str = "true.csv", predict_csv: str = "predict.csv",
                   output_dir: str = "campaign_figure") -> None:
    """
    Plot a pie chart comparing True Positives (TP) and False Positives (FP)
    between two CSV files with columns ['Entity1', 'Entity2'], and save the figure
    tightly as a PNG named after the alignment path (excluding last component).
    """

    # load csv
    gt = pd.read_csv(true_csv)
    pred = pd.read_csv(predict_csv)

    # convert to sets
    gt_set = set(zip(gt["Entity1"], gt["Entity2"]))
    pred_set = set(zip(pred["Entity1"], pred["Entity2"]))

    # compute metrics
    tp = gt_set & pred_set
    fp = pred_set - gt_set
    tp_n, fp_n = len(tp), len(fp)

    # prepare data
    sizes = [tp_n, fp_n]
    labels = ["TP", "FP"]

    cmap = plt.get_cmap("tab10")
    colors = [cmap(0), cmap(1)]

    # plot
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(
        sizes,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 11, "color": "white"},
        wedgeprops={"edgecolor": "white"}
    )
    ax.legend(
        labels,
        loc="upper left",
        # bbox_to_anchor=(0.5, 1.04),
        # ncol=2,
        # frameon=False,
        fontsize=12
    )
    ax.axis("equal")  # ensure the pie is a circle

    # fix layout
    plt.gcf().tight_layout(pad=0)

    # create output folder
    os.makedirs(output_dir, exist_ok=True)

    # build filename (exclude last folder)
    parts = alignment.strip("/").split("/")
    if len(parts) > 1:
        filename = "-".join(parts[:-1]) + ".png"
    else:
        filename = parts[0] + ".png"

    output_path = os.path.join(output_dir, filename)

    # save and show figure
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
    plt.show()

    print(f"Figure saved tightly to: {output_path}")



if __name__ == '__main__':

    # generate true.csv
    find_reference(align_path, "true.csv")

    # generate predict.csv
    e1_list_class, e2_list_class, e1_list_property, e2_list_property = find_all_entities()
    set1 = {get_entity_name(x,o1,o1_is_code) for x in e1_list_class}
    set2 = {get_entity_name(x,o2,o2_is_code) for x in e2_list_class}
    # step 1: create mappings from cleaned -> original
    map1 = {util.cleaning(x): x for x in set1}
    map2 = {util.cleaning(x): x for x in set2}
    # step 2: find intersection of cleaned keys
    common_cleaned = set(map1.keys()) & set(map2.keys())
    # step 3: create (original1, original2) pairs
    pairs = [(map1[k], map2[k]) for k in common_cleaned]
    # step 4: save pairs to CSV
    df = pd.DataFrame(pairs, columns=["Entity1", "Entity2"])
    df.to_csv("predict.csv", index=False, encoding="utf-8")

    # draw pie chart
    plot_tp_fp_pie("true.csv", "predict.csv")