## TODO:
Call Huanyu for approval for trivial reference.

## Important Notice:
This repository contains the source code, resources, and instructions to reproduce the experiments for the PVLDB 2025 paper: `Agent-OM: Leveraging LLM Agents for Ontology Matching` 
- For technical issues, please submit a GitHub Issue.  
- For feature discussion or potential extensions, please join our discussion group: https://groups.google.com/g/agent-om

## Quick Start:

### 1. Install Databases:
- Install PostgreSQL: https://www.postgresql.org/download/  
- Install pgvector: https://github.com/pgvector/pgvector  
- (Optional) Install pgAdmin: https://www.pgadmin.org/download/  
```
psql –version
sudo -u postgres psql
alter user postgres password 'postgres'  
sudo apt install postgresql-15-pgvector  
```

### 2. Install Packages:
- Required packages:
```
pip install pandas  
pip install langchain[all]  
pip install openai  
pip install rdflib  
pip install sentence-transformers   
pip install python-dotenv  
pip install pyenchant  
pip install tiktoken  
```
- Optional packages:
```
pip install google-api-python-client  
pip install wikipedia  
pip install faiss-gpu  
pip install deeponto  
pip install pypdf
```
- Versions: please check the file `requirement.txt`.

### 3. Setup OpenAI API:
- Your OpenAI API key can be found in this link: https://platform.openai.com/api-keys
- Create a file named as `.env` and write:
```python
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### 4. Setup Matching Task:

- Set your alignment in the file `run_config.py`: context, o1_is_code, o2_is_code, and alignment.  
For example, if you would like to run the CMT-Conference alignment, then the settings are:
```python
context = "conference"
alignment = "conference/cmt-conference/component/"
o1_is_code = False
o2_is_code = False
```
- (Optional) You can uncomment the following code in the file `om_ontology_to_csv.py` to use LLMs setting the variables o1_is_code and o2_is_code.
```python
import run_config as config
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def check_name_or_code(entity):
    prompt = PromptTemplate(
        input_variables=["entity"],
        template="Is {entity} a unique identifier or code? Please answer True if yes, False if not or unknown."
    )
    llm = config.llm
    chain = LLMChain(llm=llm, prompt=prompt)
    output = chain.run({'entity': entity}).strip()
    return output
```

- Set your matching hyperparameters in the file `run_config.py`: similarity_threshold and top_k.  
For example, if you would like to set the similarity_threshold = 0.80 and top_k = 3, then the settings are:
```python
similarity_threshold = 0.80
top_k = 3
# num_matches is a variable to limit the results in the database
# you can select any number to fit your database (the default setting is 50)
num_matches = 50
```

### 5. Run Experiment:
- Run the script: `python run_config.py`.  
- The result of the experiment will be stored in the folder `alignment`.  
- The evaluation of the experiment will be stored in the file `result.csv`.  

## Repository Structure:

### 1. Data:
- `data`: store the data from three OAEI tracks: conference, anatomy, and mse.

### 2. Experiment:
- `om_ontology_to_csv.py`: Retrival Agent Part 1.  
- `om_csv_to_database.py`: Retrival Agent Part 2.  
- `om_data_base_matching.py`: Matching Agent.  
- `run_config.py`: main function of the project.  
- `run_series_conference.py`: run all the conference alignment at one time.  
- `run_series_similarity.py`: run different similarity thresholds for one alignment at one time.  
- `util.py`: util component of the project.
- `alignment`: store experiment results.  
- `llm_matching.py`: examples using purely LLMs (without agent) for general matching tasks.  
- `llm_om.py`: an example of using purely LLMs (without agent) for ontology matching.  

FAQ(s):  
(1) Why Retrival Agent has two parts `om_ontology_to_csv.py` and `om_csv_to_database.py`?  
Answer: You can simply combine these two parts together. We decompose this into two parts to make it easy to debug the issue may happen in the database storge.  
(2) How to use the file`run_series_conference.py`?  
Answer: Please uncomment the following code in the file `run_config.py`:
```python
import os
if os.environ.get('../alignment'):
    alignment = os.environ['alignment']
```
(3) How to use the file`run_series_similarity.py`?  
Answer: Please set the variables in the file `run_series_similarity.py`.  
For example, if you would like to check the similarities [1.00, 0.95, ..., 0.55, 0.50], then the settings are:
```python
start = 1.00
end = 0.50
step = -0.05
```

### 3. Evaluation:
- `generate_conference_benchmark.py`: generate the OAEI Conference Track results.  
- `generate_anatomy_mse_benchmark.py`: generate the OAEI Anatomy Track and MSE Track results.  
- `benchmark_2022`: compare Agent-OM with OAEI 2022 results.  
- `benchmark_2023`: compare Agent-OM with OAEI 2023 results.  
You may find a slight different for each run, it is because:  
https://community.openai.com/t/run-same-query-many-times-different-results/140588

### 4. Visualisation:
- `draw_benchmark.ipynb`: visualise the result of benchmark.  
- `draw_ablation_study.ipynb`: visualise the result of ablation study.  
- `result_fig`: store visualisation results.  

Our new visualisation is inspired by the following references:  
- https://joernhees.de/blog/2010/07/22/precision-recall-diagrams-including-fmeasure/  
- https://towardsai.net/p/l/precision-recall-curve

## Debugging Log:
We have created a debugging log for this project. [Click the link here](LOG.md).

## Code References:
A copy can be found in the `code_references`.
- https://colab.research.google.com/github/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/postgres/pgvector/notebooks/pgvector_gen_ai_demo.ipynb 


## Acknowledgements:
- The authors claim no responsibility for the AI-generated content, which does not express the views of the authors.  
- The authors would like to thank the organisers of the Ontology Alignment Evaluation Initiative (OAEI) Conference Track, Anatomy Track, and MSE Track, for helpful advice on reproducing the benchmarks used in this paper.  
- The authors would like to thank Associate Professor Alice Richardson of the Statistical Support Network, Australian National University, for helpful advice on the statistical analysis in this paper.  
- The authors would like to thank the Commonwealth Scientific and Industrial Research Organisation (CSIRO) for supporting this project.  

## Licence:

<!-- Which licence is best for your work? Check with the CC License chooser: https://chooser-beta.creativecommons.org/ -->

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg