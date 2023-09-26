import torch

print(torch.cuda.is_available())
print(torch.randn(1).cuda())

from deeponto.onto import Ontology, OntologyVerbaliser

# load an ontology and init the verbaliser
onto = Ontology("cmt-conference/component/cmt.owl")
verbaliser = OntologyVerbaliser(onto)

# get complex concepts asserted in the ontology
complex_concepts = onto.get_asserted_complex_classes()
print(complex_concepts)

# verbalise the first complex concept
v_concept = verbaliser.verbalise_class_expression(list(complex_concepts)[0])
print(v_concept)