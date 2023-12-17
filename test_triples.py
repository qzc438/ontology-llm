import rdflib

import config

o1=config.o1

for s, p, o in o1.triples((rdflib.URIRef("http://cmt#Meta-Reviewer"), rdflib.RDFS.comment, None)):
    print(s,p,o)