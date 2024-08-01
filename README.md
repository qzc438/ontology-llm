## Agent-OM: Leveraging LLM Agents for Ontology Matching
- The preprint of the paper is currently available at arXiv: https://arxiv.org/abs/2312.00326
- This repository contains a production version of the source code linked to the paper submitted to PVLDB 2025.
- The development version of the source code is stored at: https://github.com/qzc438/ontology-llm (access will be made available on request)

## Important Notice:
- For technical inquiries, please submit a GitHub issue.
- For feature discussion or potential extensions, please join our foundation model discussion group: https://groups.google.com/g/agent-om

## Quick Start:

### 1. Install Database:
- Install PostgreSQL: https://www.postgresql.org/download/
- Install pgAdmin: https://www.pgadmin.org/download/ (Optional for GUI access to the database)
- Install pgvector: https://github.com/pgvector/pgvector
```
psql -version
sudo -u postgres psql
alter user postgres password 'postgres'
sudo apt install postgresql-15-pgvector
```

### 2. Install Python Environment:
- Install Python: https://www.python.org/downloads/
- We report our results with Python 3.10.12: https://www.python.org/downloads/release/python-31012/

### 3. Install Python Packages:
- Install LangChain packages:
```
pip install langchain==0.2.10
pip install langchain-openai==0.1.17
pip install langchain-anthropic==0.1.20
pip install langchain-mistralai==0.1.10
pip install langchain_community=0.2.9
```
- Install other packages:
```
pip install pandas==2.0.3
pip install rdflib==7.0.0
pip install python-dotenv==1.0.1
pip install pyenchant==3.2.2
pip install tiktoken==0.6.0
pip install asyncpg==0.28.0
pip install psycopg2_binary==2.9.9
pip install pgvector==0.1.8
pip install commentjson==0.9.0
pip install transformers==4.41.1
pip install colorama==0.4.6
```
- Install visualisation packages:
```
pip install matplotlib==3.8.4
pip install notebook
pip install ipyparallel
```

### 4. Install Ollama:
- Ollama GitHub: https://github.com/ollama/ollama
  - Ollama installation: https://ollama.com/download
  - Ollama FAQs: https://github.com/ollama/ollama/blob/main/docs/faq.md
  - Link Ollama to LangChain: https://python.langchain.com/v0.1/docs/integrations/llms/ollama/
- PyTorch installation: https://pytorch.org/get-started/locally/
- Ollama installation on Linux and CUDA 11.8:
  - Install or update Ollama:
  ```
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  - Install PyTorch:
  ```
  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- Ollama models: https://ollama.com/library
  - Add a model:
  ```
  ollama pull <MODEL_NAME>
  ```
  - Find a model's metadata:
  ```
  ollama show <MODEL_NAME>
  ```
  - Remove a model:
  ```
  ollama rm <MODEL_NAME>
  ```
  - Check local models:
  ```
  ollama list
  ```
  - Update local models:
  ```
  ollama list | cut -f 1 | tail -n +2 | xargs -n 1 ollama pull
  ```
  Please check this link for further updates: https://github.com/ollama/ollama/issues/4589

### 5. Setup Large Language Models (LLMs):
- You will need API keys to interact with API-accessed commercial LLMs.
- Create a file named as `.env` and write:
```
# https://platform.openai.com/account/api-keys
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
# https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY = <YOUR_ANTHROPIC_API_KEY>
# https://console.mistral.ai/api-keys/
MISTRAL_API_KEY = <YOUR_MISTRAL_API_KEY>
```
- To protect your API keys, please add `.env` into the file `.gitignore`:
```
.env
```
- Load API keys into the file `run_config.py`:
```
import os
import dotenv

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")
```
- Select one LLM in the file `run_config.py`:
```
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_community.chat_models import ChatOllama

# load GPT models: https://platform.openai.com/docs/models/
# pricing: https://openai.com/api/pricing/
llm = ChatOpenAI(model_name='gpt-4-turbo-2024-04-09', temperature=0) # expensive
llm = ChatOpenAI(model_name='gpt-4o-2024-05-13', temperature=0)
llm = ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0)
llm = ChatOpenAI(model_name='gpt-3.5-turbo-0125', temperature=0)

# load Anthropic models: https://docs.anthropic.com/en/docs/about-claude/models
# pricing: https://www.anthropic.com/pricing#anthropic-api
llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0) # expensive
llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

# load Mistral API-accessed models: https://docs.mistral.ai/getting-started/models/
# pricing: https://mistral.ai/technology/
# default timeout = 120 is too short
llm = ChatMistralAI(model="mistral-large-2402", temperature=0, timeout=600) # expensive
llm = ChatMistralAI(model="mistral-medium-2312", temperature=0, timeout=600) # will soon be deprecated
llm = ChatMistralAI(model="mistral-small-2402", temperature=0, timeout=600)

# load Mistral open-source models: https://ollama.com/library/mistral
llm = ChatOllama(model="mistral:7b", temperature=0)

# load Llama models: https://ollama.com/library/llama3
llm = ChatOllama(model="llama3:8b", temperature=0)

# load Gemma models: https://ollama.com/library/gemma2
llm = ChatOllama(model="gemma2:9b", temperature=0)

# load Qwen models: https://ollama.com/library/qwen2
llm = ChatOllama(model="qwen2:7b", temperature=0)
```
-  Select one embeddings service in the file `run_config.py`:
```
# https://platform.openai.com/docs/guides/embeddings/embedding-models
embeddings_service = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_length = 1536
embeddings_service = OpenAIEmbeddings(model="text-embedding-3-small")
vector_length = 1536
embeddings_service = OpenAIEmbeddings(model="text-embedding-3-large")
vector_length = 3072
```

### 6. Setup Matching Task:
- Set your alignment in the file `run_config.py`. For example, if you would like to run the CMT-ConfOf alignment, then the settings are:
```
context = "conference"
o1_is_code = False
o2_is_code = False
alignment = "conference/cmt-confof/component/"
```
- Set your matching hyperparameters in the file `run_config.py`. For example, if you would like to set the similarity\_threshold = 0.90 and top\_k = 3, then the settings are:
```
similarity_threshold = 0.90
top_k = 3
```
- (Optional) Set `num_matches` in the file `run_config.py`. `num_matches` is a parameter that performs a "limit" function on the database queries. We set 50 here, but you can adjust this number to fit your database memory.
```
num_matches = 50
```

### 7. Run Experiment:
- Run the script:
```
python run_config.py
```
- The result of the experiment will be stored in the folder `alignment`.
- The performance evaluation of the experiment will be stored in the file `result.csv`.
- The cost evaluation of the experiment will be stored in the file `cost.csv`.
- The matching log of the experiment will be stored in the file `agent.log`.

## Repository Structure:

### 1. Data:
- `data`: store the data from three OAEI tracks.

### 2. Experiment:
- `om_ontology_to_csv.py`: Retrieval Agent Part 1.
- `om_csv_to_database.py`: Retrieval Agent Part 2.
- `om_database_matching.py`: Matching Agent.
- `run_config.py`: main function of the project.
- `run_series_conference.py`: run all the conference alignments at one time.
- `run_series_similarity.py`: run different similarity thresholds for one alignment at one time.
- `util.py`: util component of the project.
- `alignment`: store experiment results.
- `llm_matching.py`: examples using purely LLMs for general matching tasks.
- `llm_om_zero_shot.py`: examples of using purely LLMs without ontology information for ontology matching.
- `llm_om_few_shot.py`: examples of using purely LLMs with ontology information for ontology matching.

Frequently Asked Questions (FAQs):
- Why does the Retrieval Agent have two parts `om_ontology_to_csv.py` and `om_csv_to_database.py`?  
Answer: You can simply combine these two parts together. We decompose this into two parts to make it easy to debug any issue that may occur in the database storage.

- How do I use the file `run_series_conference.py`?  
Answer: Please uncomment the following code in the file `run_config.py`.
```
import os
if os.environ.get('alignment'):
    alignment = os.environ['alignment']
```

- How do I use the file `run_series_similarity.py`?  
Answer: Please set the variables in the file `run_series_similarity.py`.  
For example, if you would like to check the similarities [1.00, 0.95, ..., 0.55, 0.50], then the settings are:
```
start = 1.00
end = 0.50
step = -0.05
```

### 3. Evaluation:
- `generate_conference_benchmark.py`: generate the results of OAEI Conference Track.
- `generate_anatomy_mse_benchmark.py`: generate the results of OAEI Anatomy Track and OAEI MSE Track.
- `fix_multifarm_reference.py`: fix the URI issue of OAEI Multifarm Track.
- `benchmark_2022`: compare Agent-OM with the results of OAEI 2022.
- `benchmark_2023`: compare Agent-OM with the results of OAEI 2023.
- You may find a slight difference for each run. It is because: https://community.openai.com/t/run-same-query-many-times-different-results/140588

### 4. Visualisation:
- `draw_benchmark.ipynb`: visualise the results of the evaluation.
- `draw_ablation_study.ipynb`: visualise the results of the ablation study.
- `result_csv`: store the original data of the results.
- `result_figure`: store the visualisation of the results.
- Our new visualisation is inspired by the following references:
  - https://joernhees.de/blog/2010/07/22/precision-recall-diagrams-including-fmeasure/
  - https://towardsai.net/p/l/precision-recall-curve

## Debugging Log:
- We have created a debugging log for this project. [Click the link here.](DEBUGGING_LOG.md)

## Ethical Considerations:
- Agent-OM does not participate in the OAEI 2022 and 2023 campaigns.
- According to the OAEI data policy (date accessed: 2024-06-30), "OAEI results and datasets, are publicly available, but subject to a use policy similar to [the one defined by NIST for TREC](https://trec.nist.gov/results.html). These rules apply to anyone using these data." Please find more details from the official website: https://oaei.ontologymatching.org/doc/oaei-deontology.2.html
- In this paper, AI-generated content (AIGC) is labelled as "AI-generated content". AIGC can contain harmful, unethical, prejudiced, or negative content (https://docs.mistral.ai/capabilities/guardrailing/). However, ontology matching tasks only check the meaning of domain-specific terminologies, and we have not observed such content being generated.

## Code Acknowledgements:
- We use the LangChain Python package to generate LLM agents: https://api.python.langchain.com/en/latest/langchain_api_reference.html
- Our data-driven application architecture is inspired by: https://colab.research.google.com/github/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/postgres/pgvector/notebooks/pgvector_gen_ai_demo.ipynb

## Author Acknowledgements:
- The authors would like to thank Sven Hertling for curating the datasets stored in the Matching EvaLuation Toolkit (MELT) for the Ontology Alignment Evaluation Initiative (OAEI) 2022 and 2023.
- The authors would like to thank the organisers of Ontology Alignment Evaluation Initiative (OAEI) 2022 and 2023 Conference Track (Ondřej Zamazal and Lu Zhou), Anatomy Track (Mina Abd Nikooie Pour, Huanyu Li, Ying Li, and Patrick Lambrix), and MSE Track (Engy Nasr and Martin Huschka), for helpful advice on reproducing the benchmarks used in this paper.
- The authors would like to thank Jing Jiang from the Australian National University (ANU) for helpful advice on the semantic verbaliser used in this paper.
- The authors would like to thank Alice Richardson of the Statistical Support Network, Australian National University (ANU), for helpful advice on the statistical analysis in this paper.
- The authors would like to thank the Commonwealth Scientific and Industrial Research Organisation (CSIRO) for supporting this project.

## Licence:

<!-- Which licence is best for your work? Check with the CC License chooser: https://chooser-beta.creativecommons.org/ -->
<!-- https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.txt -->

Shield: [![CC BY-NC-ND 4.0][cc-by-nc-nd-shield]][cc-by-nc-nd]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-NoDerivs 4.0 International License][cc-by-nc-nd].

[![CC BY-NC-ND 4.0][cc-by-nc-nd-image]][cc-by-nc-nd]

[cc-by-nc-nd]: http://creativecommons.org/licenses/by-nc-nd/4.0/
[cc-by-nc-nd-image]: https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png
[cc-by-nc-nd-shield]: https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg
