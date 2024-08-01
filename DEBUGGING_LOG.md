### Debugging Log:
- Release initial source code [2023-09-19]

#### How to fix PyTorch "torch.cuda.is_available() = false"?
```
sudo apt-get purge nvidia-*
sudo apt-get update
sudo apt-get autoremove
sudo apt --fix-broken install
```

#### How to deal with pdAdmin "Your account is locked. Please contact admin"?
```
sudo su
apt-get install sqlite3
sqlite3 pgadmin4.db "UPDATE USER SET LOCKED = false, LOGIN_ATTEMPTS = 0 WHERE USERNAME = 'user.name@domain.com';" ".exit"
```

#### How to align the results of Agent-OM with the results of the OAEI Anatomy Track?
- Please check the function `filter_anatomy()` in the `util.py`.
  - Remove the mappings that are different from the equivalence.
  - Remove the non-distinct mappings that appear twice.
  - Remove all mappings between oboInOwl name-spaced concepts.
- For example, the following 8 mappings need to be removed from Agent-OM results:
```
<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Subset"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Subset"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Synonym"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Synonym"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
        </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#DbXref"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#DbXref"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#ObsoleteClass"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#ObsoleteClass"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#SynonymType"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#SynonymType"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Definition"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#Definition"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://www.geneontology.org/formats/oboInOwl#ObsoleteProperty"/>
        <entity2 rdf:resource="http://www.geneontology.org/formats/oboInOwl#ObsoleteProperty"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>

<map>
    <Cell>
        <entity1 rdf:resource="http://mouse.owl#UNDEFINED_part_of"/>
        <entity2 rdf:resource="http://human.owl#UNDEFINED_part_of"/>
        <measure rdf:datatype="xsd:float">1.0</measure>
        <relation>=</relation>
    </Cell>
</map>
```

#### How to find the trivial reference in the OAEI Anatomy Track?
- Please use the file `trivial.rdf` in the folder `benchmark_2022/anatomy` and `benchmark_2023/anatomy`.
- This file will be publicly available together with the source data in OAEI 2024.

#### How to align the results of Agent-OM with the results of the OAEI MSE Track Test Case 1?
- This track also contains the subsumption mappings in the reference alignment file `reference-old.xml`.
- We set all subsumption mappings to None and reproduce the reference alignment file `reference.xml`.

#### How to fix if some results are unreproducible?
- Please check the root IRI of the mapping file, and it should follow the format specification: https://moex.gitlabpages.inria.fr/alignapi/format.html
- You need to add the character `"#"` in the root IRI of the mapping file `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"`.

#### How to define a unique entity ID?
- Adding the prefixes "source:" and "target:" can distinguish the terms, but LLM considers ":" as a separator, so sometimes it may ignore "source:" and "target:".
- Using the URI for an entity ID is incorrect because both the source and target ontologies can reuse a term with the same URI.
- To ensure a unique entity ID, we propose the following structure: `[entity_id] = [INDEX]-[source_or_target]-[entity_type]-[entity_name]`

#### How to handle the null value of LLM output?
- For null values, LLM may generate a sentence rather than follow the JSON format: "I couldn't find an equivalent entity for [entity] through syntactic, lexical, or graphical matching."
  - `None` and `Not Available` frequently get errors.
  - `N/A` and `Missing` sometimes get errors.
- To ensure no error is produced for the null value, we propose the following structure:
  - In the retrieval process, we replace the null value with the keyword `null_value_sentence` defined in `run_config.py`.
  - In the database storage, we replace the `null_value_sentence` with the null value.
  - In the matching process, we replace the null value with the keyword `null_value_matching` defined in `run_config.py`, but mappings with the keyword will be filtered in the parameter `rankings`.

#### How to invoke the function calling in LLMs?
- Do not use the special character ":" for your input. LLMs may consider this symbol as a separator and return only the name.
- Do not use the special character "." along with your input. LLMs will treat "{entity}." (with a full stop) as the input.
- Function Declaration:
  - We suggest using a single word for the function name and argument name.
  - We suggest using a verb for function description.
  - The camel case is fine, but the snake case is wrong.
- Function Prompt:
  - Main content from: https://python.langchain.com/v0.1/docs/use_cases/tool_use/prompting/
  - Add one sentence from: https://medium.com/pythoneers/power-up-ollama-chatbots-with-tools-113ed8229a7a
  - We apply some slight changes to fit different LLM models.
- It is possible to add tool error handling: https://python.langchain.com/v0.1/docs/use_cases/tool_use/tool_error_handling/

#### Prompt Testbed:

- Please consider using the following examples to test your retrieving prompt:

| Track      | Entity                                                                | Description                                  |
|------------|-----------------------------------------------------------------------|----------------------------------------------|
| Conference | entity_list = ["http://cmt#Meta-Reviewer"]                            | test extra information                       |
| Conference | entity_list = ["http://cmt#Meta-Review"]                              | test return wrong tool key for tool          |
| Conference | entity_list = ["http://cmt#acceptedBy"]                               | test return the key "tool" instead of "name" |
| Conference | entity_list = ["http://conference#Organization"]                      | test no semantic information                 |
| Conference | entity_list = ["http://conference#Important_dates"]                   | test name format                             |
| Conference | entity_list = ["http://conference#User"]                              | test name using keyword                      |
| Anatomy    | entity_list = ["http://www.geneontology.org/formats/oboInOwl#DbXref"] | test name using keyword                      |

- Please consider using the following examples to test your matching prompt:

| Track      | Entity                                    | Description                                                     |
|------------|-------------------------------------------|-----------------------------------------------------------------|
| Conference | e1_list = ["http://cmt#Bid"]              | test all null value                                             |
| Conference | e1_list = ["http://cmt#Conference"]       | test matching validator                                         |
| Conference | e1_list = ["http://cmt#Meta-Reviewer"]    | test matching validator                                         |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000096"] | test one null value                                             |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0001017"] | test all null value                                             |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000013"] | test hemolymphoid system and Hematopoietic_and_Lymphatic_System |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0000006"] | test head/neck and Head_and_Neck                                |
| Anatomy    | e1_list = ["http://mouse.owl#MA_0001742"] | test sensitive word                                             |

- We use a strong validator (e.g. "equivalent" and "identical") to identify the equivalence relationship.
- In some cases, a weak validator (e.g. "interchangeable") is better.
- Please consider using the following example to test your validation prompt:

| Track      | Entity1                                  | Entity2                                      |
|------------|------------------------------------------|----------------------------------------------|
| Conference | e1_list = ["http://cmt#SubjectArea"]     | e2_list = ["http://cmt#Topic"]               |
| Conference | e1_list = ["http://cmt#ConferenceChair"] | e2_list = ["http://cmt#Chair"]               |
| Conference | e1_list = ["http://cmt#Document"]        | e2_list = ["http://cmt#Conference_document"] |
