### Debugging Log:

- [X] Release source code [April 15, 2024]

#### 1. How to fix *torch.cuda.is_available() = false*?
```cmd
sudo apt-get purge nvidia-*
sudo apt-get update
sudo apt-get autoremove
sudo apt --fix-broken install
```

#### 2. How to fix the results so that the Anatomy Track are in line with the OAEI results?
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

#### 3. How to fix the results so that the MSE Track Test Case 1 are in line with the OAEI results?
- This track also contains the subsumption mappings in the reference alignment file `reference-old.xml`.
- We set all subsumption mappings to None and reproduce the reference alignment file `reference.xml`.

#### 4. How to fix the results of Matcha that are unreproducible?
- Unlike other systems, the root IRI of Matcha's mapping file is `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"`.
- We remove the character `"#"` the root IRI of the mapping file `xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"`.

#### 5. How to fix the LLM output formatting error?
- We recommend using the output-parsers: https://python.plainenglish.io/langchain-in-chains-7-output-parsers-e1a2cdd40cd3
- For the NULL value, we suggest using "N/A", as "None" or "Null" will miss the "," afterward in the JSON format.
