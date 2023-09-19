import rdflib
import util

def find_uri(ontology):
    for ns_prefix, namespace in ontology.namespaces():
        if not ns_prefix:
            return namespace
    return ""

o1 = rdflib.Graph().parse("cmt-conference/component/source.xml", format="xml")
o2 = rdflib.Graph().parse("cmt-conference/component/target.xml", format="xml")
o1_base_iri = find_uri(o1)
o2_base_iri = find_uri(o2)
l1 = len(o1_base_iri)
l2 = len(o2_base_iri)

e1_list_class = list()
e2_list_class = list()
for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
    if x[l1:] and "#" in x:
        e1_list_class.append(x[l1:])
for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
    if y[l2:] and "#" in y:
        e2_list_class.append(y[l2:])

# print(e1_list_class)
# print(e2_list_class)

with open('initial.txt', 'w') as f:
    for e1 in e1_list_class:
        for e2 in e2_list_class:
            if util.cleaning(e1) == util.cleaning(e2):
                f.write("%s in the source ontology is equivalent to %s in the target ontology." % (util.cleaning(e1), util.cleaning(e2)))
                f.write('\n')

