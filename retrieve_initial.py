import rdflib
import util

if __name__ == '__main__':
    o1 = rdflib.Graph().parse("cmt-conference/component/source.xml", format="xml")
    o2 = rdflib.Graph().parse("cmt-conference/component/target.xml", format="xml")
    o1_base_iri = util.find_uri(o1)
    o2_base_iri = util.find_uri(o2)
    l1 = len(o1_base_iri)
    l2 = len(o2_base_iri)

    o1_prefix = rdflib.Namespace(o1_base_iri)
    o2_prefix = rdflib.Namespace(o2_base_iri)
    o1.bind("cmt", o1_prefix)
    o2.bind("conference", o2_prefix)

    e1_list_class = list()
    e2_list_class = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if x[l1:] and "#" in x:
            class_name = o1.namespace_manager.qname(str(x))
            e1_list_class.append(class_name)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        if y[l2:] and "#" in y:
            class_name = o2.namespace_manager.qname(str(y))
            e2_list_class.append(class_name)
    print(e1_list_class)
    print(e2_list_class)

    e1_list_property = list()
    e2_list_property = list()
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if x[l1:] and "#" in x:
            property_name = o1.namespace_manager.qname(str(x))
            e1_list_property.append(property_name)
    for x in o1.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if x[l1:] and "#" in x:
            property_name = o1.namespace_manager.qname(str(x))
            e1_list_property.append(property_name)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty):
        if y[l2:] and "#" in y:
            property_name = o2.namespace_manager.qname(str(y))
            e2_list_property.append(property_name)
    for y in o2.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if y[l2:] and "#" in y:
            property_name = o2.namespace_manager.qname(str(y))
            e2_list_property.append(property_name)
    print(e1_list_property)
    print(e2_list_property)

    with open('rag/initial.txt', 'w') as f:
        for e1 in e1_list_class:
            for e2 in e2_list_class:
                if util.cleaning(e1.split(":")[-1]) == util.cleaning(e2.split(":")[-1]):
                    f.write("%s owl:equivalentClass %s." % (e1, e2))
                    f.write('\n')
