### Debugging Log:
- [X] Release initial source code [Sep 19, 2023]
- [X] Fix JSON output issue [Apr 25, 2024]
- [X] Fix NULL output issue [Apr 25, 2024]

#### How to fix *torch.cuda.is_available() = false*?
```cmd
sudo apt-get purge nvidia-*
sudo apt-get update
sudo apt-get autoremove
sudo apt --fix-broken install
```

#### How to fix the results so that the Anatomy Track are in line with the OAEI results?
- Remove the mappings different from the equivalence.  
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
- Please use the file `trivial.rdf`. This file will be publicly available together with the source ontologies and alignment in OAEI 2024.

#### How to fix the results so that the MSE Track Test Case 1 are in line with the OAEI results?
- This track also contains the subsumption mappings in the reference alignment file `reference-old.xml`.
- We set all subsumption mappings to None and reproduce the reference alignment file `reference.xml`.

#### How to fix the results of Matcha that are unreproducible?
- Unlike other systems, the root IRI of Matcha's mapping file is `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"`.
- We remove the character `"#"` the root IRI of the mapping file `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"`.

#### How to define a unique entity ID?
- Adding the prefixes "source:" and "target:" can distinguish the terms, but LLM considers ":" as a separator, so sometimes it may ignore "source:" and "target:".
- Using the URI for an entity ID is incorrect because both the source and target ontologies can reuse a term with the same URI.
- To ensure a unique entity ID, we propose the following structure: [entity_id] = [source_or_target]-[entity_type]-[entity_name].

#### How to fix the formatting error in the LLM output?
- We recommend using the output parsers to avoid generating random results from LLM.
- Response Schema is a good tool to format the output, but you need to:
  - Use the same name for function, function description, schema name, and schema description.
  - Exclude the comments in your JSON.
  ```python
  json_no_comments = re.sub(r'//.*', '', output)
  ```
- This approach is currently unable to handle cases where the content contains "//". To manually resolve this issue, you need:
  - Ensure to remove the JSON markdown both before and after the structure. Please remember to use the strip() function.
  ```python
  if output.strip().startswith("```json") and output.strip().endswith("```"):
      output = output.strip()[7:-3]
  ```
  - Use commentjson library to remove the comments.
  ```python
  import commentjson
  output_dict = commentjson.loads(output)
  print("output_dict:", output_dict)
  ```
  - Set a default value to handle the case where the key for the null value is not returned.
  ```python
  syntactic_information = output_dict.get('syntactic_retrieving', null_value)
  ```

#### How to handle the null value of LLM output?
- For null values, LLM may generate a sentence rather than follow the JSON format: "I couldn't find an equivalent entity for [entity] through syntactic, lexical, or graphical matching."
  - `None` and `Not Available` frequently get error. 
  - `N/A` and `Missing` sometimes get error.
- To ensure no error produced for the null value, we propose the following structure:
  - In the retrieval process, we replace the null value with the keyword `Information is not available.`.
  - In the database storage, we replace the keyword with the null value.
  - In the matching process, we replace the null value with the keyword `Entity-Unmatched`, but mappings with the keyword will be filtered in the parameter `rankings`.