import amrlib
stog = amrlib.load_stog_model()
graphs = stog.parse_sents(['This is a test of the system.', 'This is a second sentence.'])
for graph in graphs:
    print(graph)

import amrlib
gtos = amrlib.load_gtos_model()
sents, _ = gtos.generate(graphs)
for sent in sents:
    print(sent)