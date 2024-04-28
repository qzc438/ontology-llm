## Agent-OM: Leveraging LLM Agents for Ontology Matching
- The preprint of the paper is currently available at arXiv: https://arxiv.org/abs/2312.00326
- This repository contains the source code linked to the paper. The original version of this work can be found in: https://github.com/qzc438/ontology-llm (access will be made available on request)

## Important Notice:
- For technical inquiries, please submit a GitHub issue.
- For feature discussion or potential extensions, please join our foundation model discussion group: https://groups.google.com/g/agent-om

## Quick Start:

### 1. Install Databases:
- Install PostgreSQL: https://www.postgresql.org/download/
- Install pgAdmin: https://www.pgadmin.org/download/ (optional for GUI access to the database) 
- Install pgvector: https://github.com/pgvector/pgvector
```
psql –version
sudo -u postgres psql
alter user postgres password 'postgres'
sudo apt install postgresql-15-pgvector
```

### 2. Install Python:
- Python 3.10: https://www.python.org/downloads/release/python-31012/ (recommend version 3.10.12)

### 3. Install Python Packages:
```
pip install langchain==0.1.14
pip install langchain-openai==0.1.1
pip install pandas==2.0.3
pip install rdflib==7.0.0
pip install python-dotenv==1.0.1
pip install pyenchant==3.2.2
pip install tiktoken==0.6.0
pip install asyncpg==0.28.0
pip install psycopg2_binary==2.9.9
pip install pgvector==0.1.8
pip install JSON-minify==0.3.0
```
```
pip install matplotlib==3.8.4
pip install notebook
pip install ipyparallel
```

### 4. Setup OpenAI API:
- You will need an OpenAI API key to interact with GPT models: https://platform.openai.com/api-keys
- Create a file named as `.env` and write:
```plaintext
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
```

### 5. Setup Large Language Model (LLM):
- Set the LLM in the file `run_config.py`: `llm_model_name`.
```python
# GPT-3.5
llm_model_name = 'gpt-3.5-turbo'
# Agent-OM also supports GPT-4, but our experiments are based on 'gpt-3.5-turbo'
# GPT-4
# llm_model_name = 'gpt-4-turbo'
```

### 6. Setup Matching Task:
- Set your alignment in the file `run_config.py`: `context`, `o1_is_code`, `o2_is_code`, and `alignment`.  
For example, if you would like to run the CMT-Conference alignment, then the settings are:
```python
context = "conference"
alignment = "conference/cmt-conference/component/"
o1_is_code = False
o2_is_code = False
```
- Set your matching hyperparameters in the file `run_config.py`: `similarity_threshold` and `top_k`.  
For example, if you would like to set the similarity_threshold = 0.80 and top_k = 3, then the settings are:
```python
similarity_threshold = 0.80
top_k = 3
```
- `num_matches` is a parameter performs a "limit" function on the database queries. We set 50 here, but you can adjust this number to fit your database memory.
```python
num_matches = 50
```

### 7. Run Experiment:
- Run the script: `python run_config.py`.
- The result of the experiment will be stored in the folder `alignment`.
- The evaluation of the experiment will be stored in the file `result.csv`.

## Repository Structure:

### 1. Data:
- `data`: store the data from three OAEI tracks: Conference Track, Anatomy Track, and MSE Track.

### 2. Experiment:
- `om_ontology_to_csv.py`: Retrieval Agent Part 1.
- `om_csv_to_database.py`: Retrieval Agent Part 2.
- `om_database_matching.py`: Matching Agent.
- `run_config.py`: main function of the project.
- `run_series_conference.py`: run all the conference alignments at one time.
- `run_series_similarity.py`: run different similarity thresholds for one alignment at one time.
- `util.py`: util component of the project.
- `alignment`: store experiment results.
- `llm_matching.py`: examples using purely LLMs (without agents) for general matching tasks.
- `llm_om.py`: an example of using purely LLMs (without agents) for ontology matching.

Frequently Asked Questions (FAQs):  
(1) Why does the Retrieval Agent have two parts `om_ontology_to_csv.py` and `om_csv_to_database.py`?  
Answer: You can simply combine these two parts together. We decompose this into two parts to make it easy to debug the issue that may happen in the database storage.  
(2) How do I use the file`run_series_conference.py`?  
Answer: Please uncomment the following code in the file `run_config.py`.
```python
import os
if os.environ.get('alignment'):
    alignment = os.environ['alignment']
```
(3) How do I use the file`run_series_similarity.py`?  
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

You may find a slight difference for each run, it is because:  
https://community.openai.com/t/run-same-query-many-times-different-results/140588

### 4. Visualisation:
- `draw_benchmark.ipynb`: visualise the result of the evaluation.
- `draw_ablation_study.ipynb`: visualise the result of the ablation study.
- `result_fig`: store visualisation results.

Our new visualisation is inspired by the following references:  
- https://joernhees.de/blog/2010/07/22/precision-recall-diagrams-including-fmeasure/
- https://towardsai.net/p/l/precision-recall-curve

## Debugging Log:
We have created a debugging log for this project. [Click the link here.](DEBUGGING_LOG.md)

## Prompt Instruction:
We have created a prompt instruction for this project. [Click the link here.](PROMPT_INSTRUCTION.md)

## Code Acknowledgements:
- The LangChain API is used for generating LLM agents: https://api.python.langchain.com/en/latest/langchain_api_reference.html
- Our data-driven application architecture is inspired by: https://colab.research.google.com/github/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/postgres/pgvector/notebooks/pgvector_gen_ai_demo.ipynb
- The LLM output parsers is instructed by: https://medium.com/python-in-plain-english/langchain-in-chains-7-output-parsers-e1a2cdd40cd3

## Acknowledgements:
- AI-generated content is labelled as "AI-generated content". The authors claim no responsibility for the AI-generated content marked in this paper, which does not express the views of the authors.
- The authors would like to thank the organisers of Ontology Alignment Evaluation Initiative (OAEI) 2022 and 2023 Conference Track (Ondřej Zamazal and Lu Zhou), Anatomy Track (Mina Abd Nikooie Pour, Huanyu Li, Ying Li and Patrick Lambrix), and MSE Track (Engy Nasr and Martin Huschka), for helpful advice on reproducing the benchmarks used in this paper.
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