import dotenv
import os
import rdflib
import util
import agent_rag_old
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

if __name__ == '__main__':
    # load openai API
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    # define llm
    llm = OpenAI(temperature=0)
    prompt = PromptTemplate(
        input_variables=["background", "entity"],
        template="{background}. What is the meaning of {entity} in the context of conference?",
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    # find all entities
    o1_path = "cmt-conference/component/source.xml"
    o2_path = "cmt-conference/component/target.xml"

    e1_list_class, e2_list_class, e1_list_property, e2_list_property = agent_match.find_all_entities(o1_path, o2_path)

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

    # find all labels
    name_with_label_dict = {}
    for s, p, o in o1.triples((None, rdflib.RDFS.comment, None)):
        name = o1.namespace_manager.qname(str(s))
        label = str(o)
        name_with_label_dict[name] = label
    for s, p, o in o2.triples((None, rdflib.RDFS.comment, None)):
        name = o2.namespace_manager.qname(str(s))
        label = str(o)
        name_with_label_dict[name] = label
    print(name_with_label_dict)

    with open('rag/lexical.txt', 'w') as f:
        for e in e1_list_class+e2_list_class + e1_list_property + e2_list_property:
            if e in name_with_label_dict.keys():
                lexical_information = chain.run({
                    'background': name_with_label_dict[e],
                    'entity': e.split(":")[-1]
                }).strip()
            else:
                lexical_information = chain.run({
                    'background': "",
                    'entity': e.split(":")[-1]
                }).strip()
            f.write("The description of %s is %s" % (e, lexical_information))
            f.write('\n')
