import rdflib
import csv
import util
import os


alignCell = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmentCell')
alignEntity1 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity1')
alignEntity2 = rdflib.term.URIRef('http://knowledgeweb.semanticweb.org/heterogeneity/alignmententity2')


def find_alignment(align_path, o1_path, o2_path, y_true_path):
    # load alignment file
    align = rdflib.Graph().parse(align_path)
    # load ontologies
    o1 = rdflib.Graph().parse(o1_path)
    o2 = rdflib.Graph().parse(o2_path)
    o1_base_iri = util.find_uri(o1)
    o2_base_iri = util.find_uri(o2)
    l1 = len(o1_base_iri)
    l2 = len(o2_base_iri)
    # create true csv
    util.create_document(y_true_path, header=['Entity1', 'Entity2'])
    # write alignment into csv
    with open(y_true_path, "a+", newline='') as f1:
        writer = csv.writer(f1)
        for s in align.subjects(rdflib.RDF.type, alignCell):
            e1 = align.value(s, alignEntity1, None)[l1:]
            e2 = align.value(s, alignEntity2, None)[l2:]
            list_pair = [e1, e2]
            writer.writerow(list_pair)


def find_all_entities(o1_path, o2_path):
    o1 = rdflib.Graph().parse(o1_path)
    o2 = rdflib.Graph().parse(o2_path)
    o1_base_iri = util.find_uri(o1)
    o2_base_iri = util.find_uri(o2)
    l1 = len(o1_base_iri)
    l2 = len(o2_base_iri)
    # add entities into list
    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x[l1:] and "#" in x:
            e1_list_class.append(x[l1:])
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y[l2:] and "#" in y:
            e2_list_class.append(y[l2:])
    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x[l1:] and "#" in x:
            e1_list_property.append(x[l1:])
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x[l1:] and "#" in x:
            e1_list_property.append(x[l1:])
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y[l2:] and "#" in y:
            e2_list_property.append(y[l2:])
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y[l2:] and "#" in y:
            e2_list_property.append(y[l2:])

    return e1_list_class, e2_list_class, e1_list_property, e2_list_property