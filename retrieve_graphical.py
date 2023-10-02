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

    with open('rag/graphical.txt', 'w') as f:
        for triple in o1:
            sub = str(triple[0])
            pre = str(triple[1])
            obj = str(triple[2])
            if "#" in sub and "#" in pre and "#" in obj:
                sub = o1.namespace_manager.qname(sub)
                pre = o1.namespace_manager.qname(pre)
                obj = o1.namespace_manager.qname(obj)
                f.write("%s %s %s." % (sub, pre, obj))
                f.write('\n')

    # for triple in o1:
    #     # print(triple[0], triple[1], triple[2])
    #     sub = str(triple[0])
    #     pre = str(triple[1])
    #     obj = str(triple[2])
    #     # labels
    #     if pre.split("#")[1] and pre.split("#")[1] == "comment":
    #         f.write("In the source ontology, %s is %s." % (util.cleaning(sub.split("#")[1]), util.cleaning(obj)))
    #         f.write('\n')
    #     if "#" in sub and "#" in pre and "#" in obj:
    #         # class or property
    #         if pre.split("#")[1] and pre.split("#")[1] == "type":
    #             f.write("In the source ontology, %s is %s." % (util.cleaning(sub.split("#")[1]), util.cleaning(obj.split("#")[1])))
    #             f.write('\n')
    #         # relations
    #         else:
    #             f.write("In the source ontology, %s %s %s." % (util.cleaning(sub.split("#")[1]), pre.split("#")[1], util.cleaning(obj.split("#")[1])))
    #             f.write('\n')
    #     # axioms
    #     else:
    #         f.write('\n')
    #
    # for triple in o2:
    #     sub = str(triple[0])
    #     pre = str(triple[1])
    #     obj = str(triple[2])
    #     # labels
    #     if pre.split("#")[1] and pre.split("#")[1] == "comment":
    #         f.write("In the source ontology, %s is %s." % (util.cleaning(sub.split("#")[1]), util.cleaning(obj)))
    #         f.write('\n')
    #     # relations
    #     if "#" in sub and "#" in pre and "#" in obj:
    #         # class or property
    #         if pre.split("#")[1] and pre.split("#")[1] == "type":
    #             f.write("In the source ontology, %s is %s." % (
    #             util.cleaning(sub.split("#")[1]), util.cleaning(obj.split("#")[1])))
    #             f.write('\n')
    #         else:
    #             f.write("In the source ontology, %s %s %s." % (
    #             util.cleaning(sub.split("#")[1]), pre.split("#")[1], util.cleaning(obj.split("#")[1])))
    #             f.write('\n')
    #     # axioms
    #     else:
    #         f.write('\n')
