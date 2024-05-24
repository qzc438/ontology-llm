### Debugging Log:
- [X] Release initial source code [Sep 19, 2023]
- [X] Fix the JSON output issue [Apr 25, 2024]
- [X] Fix the NULL output issue [Apr 25, 2024]

#### How to fix *torch.cuda.is_available() = false*?
```cmd
sudo apt-get purge nvidia-*
sudo apt-get update
sudo apt-get autoremove
sudo apt --fix-broken install
```

#### How to fix the results so that the results of Anatomy Track are in line with the OAEI results?
- Remove the mappings that are different from the equivalence.  
- Remove the non-distinct mappings that appear twice.  
- Remove all mappings between oboInOwl name-spaced concepts.  
For example, the following 8 mappings need to be removed from Agent-OM results:
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

#### How to find the trivial reference in the Anatomy Track?
- Please use the file `trivial.rdf`. This file will be publicly available together with the source data in OAEI 2024.

#### How to fix the results so that the MSE Track Test Case 1 are in line with the OAEI results?
- This track also contains the subsumption mappings in the reference alignment file `reference-old.xml`.
- We set all subsumption mappings to None and reproduce the reference alignment file `reference.xml`.

#### How to fix the results of Matcha that are unreproducible?
- Unlike other systems, the root IRI of Matcha's mapping file is `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"`.
- We remove the character `"#"` in the root IRI of the mapping file `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"`.

#### How to define a unique entity ID?
- Adding the prefixes "source:" and "target:" can distinguish the terms, but LLM considers ":" as a separator, so sometimes it may ignore "source:" and "target:".
- Using the URI for an entity ID is incorrect because both the source and target ontologies can reuse a term with the same URI.
- To ensure a unique entity ID, we propose the following structure: `[entity_id] = [index+1]-[source_or_target]-[entity_type]-[entity_name]`

#### How to fix the formatting error in the LLM output?
- We recommend using the output parsers to avoid generating random results from LLM.
- Response Schema is a good tool to format the output, but you need to:
  - Use the same name for function, function description, schema name, and schema description.
  - Keep the key as simple as possible. The key `syntactic` is better than `syntactic_retrieving`.
  - Exclude the comments from your JSON.
  ```python
  import re
  json_no_comments = re.sub(r'//.*', '', output)
  ```
- This approach is currently unable to handle cases where the content contains "//". To manually resolve this issue, you need:
  - Ensure to remove the JSON markdown both before and after the structure, and other irrelevant text. 
  ```python
  if "```json" in output and "```" in output:
      start_index = output.find("```json") + 7
      end_index = output.rfind("```")
      output = output[start_index:end_index].strip()
  ```
  - Use commentjson library to remove the comments.
  ```python
  import commentjson
  output_dict = commentjson.loads(output)
  ```
  - Set a default value to handle the case where the key for the null value is not returned.
  ```python
  syntactic_information = output_dict.get('syntactic', null_value_sentence)
  ```

#### How to handle the null value of LLM output?
- For null values, LLM may generate a sentence rather than follow the JSON format: "I couldn't find an equivalent entity for [entity] through syntactic, lexical, or graphical matching."
  - `None` and `Not Available` frequently get errors. 
  - `N/A` and `Missing` sometimes get errors.
- To ensure no error is produced for the null value, we propose the following structure:
  - In the retrieval process, we replace the null value with the keyword `null_value_sentence` defined in `run_config.py`.
  - In the database storage, we replace the `null_value_sentence` with the null value.
  - In the matching process, we replace the null value with the keyword `null_value_matching` defined in `run_config.py`, but mappings with the keyword will be filtered in the parameter `rankings`.


#### We recommend use a single word for tool name, camel case is fine, snake case is wrong.

#### How to deal with pdAdmin "Your account is locked. Please contact admin"?
- sudo su
- apt-get install sqlite3
- sqlite3 pgadmin4.db "UPDATE USER SET LOCKED = false, LOGIN_ATTEMPTS = 0 WHERE USERNAME = 'user.name@domain.com';" ".exit"
