## Agent-OM: Leveraging LLM Agents for Ontology Matching
- The preprint of the paper is available at arXiv: https://arxiv.org/abs/2312.00326
- The source code, data, and/or other artifacts are available at GitHub: https://github.com/qzc438/ontology-llm

## News:
- This paper has been accepted by PVLDB 2025 (https://vldb.org/2025/).
- A production version linked to the PVLDB 2025 paper can be found in the `Releases` section.
- The slide presentation can be found in the `slide_presentation` folder.


## Important Notice:
- For technical inquiries, please submit a GitHub issue.
- For feature discussion or potential extensions, please join our foundation model discussion group: https://groups.google.com/g/agent-om
- To track the continuous development of LLMs, we propose to use the benchmark with a timestamp tag.

## Instructions:

- Our experiment was run on a Dell Alienware Aurora R15.
  - Memory: 64.0 GiB 
  - Processor: 13th Gen Intel® Core™ i9-13900KF × 32 
  - Graphics: NVIDIA GeForce RTX™ 4090 
  - Disk Capacity: 6.1 TB
- The operating system is Ubuntu 24.04.1 LTS. 
- The CUDA version is 12.2.

### 1. Install PostgreSQL Database:
- PostgreSQL: https://www.postgresql.org/download/
- pgAdmin: https://www.pgadmin.org/download/ (optional for GUI access to the database)
- pgvector: https://github.com/pgvector/pgvector
- Create a database and name it `ontology`.
- Install PostgreSQL, pgAdmin, and pgvector on Ubuntu and CUDA 12.2:
  - Install PostgreSQL: https://www.postgresql.org/download/linux/ubuntu/
  - Install pgAdmin: https://www.pgadmin.org/download/pgadmin-4-apt/
  - Install pgvector: https://github.com/pgvector/pgvector
- If the password failed:
```
psql --version
sudo -u postgres psql
alter user postgres password 'postgres';
\q
```
  - If fatal error: postgres.h: No such file or directory
```
sudo apt install postgresql-server-dev-16 (Replace 16 with your Postgres server version)
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
pip install langchain_community==0.2.9
```
- Install other packages:
```
pip install pandas==2.0.3
pip install rdflib==7.0.0
pip install nltk==3.9.1
pip install python-dotenv==1.0.1
pip install pyenchant==3.2.2
pip install tiktoken==0.7.0
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
- Deal with the blank page: https://stackoverflow.com/questions/55152948/juypter-notebook-shows-blank-page

**Author Note**
- There is a known issue with the `Enchant` and `PyEnchant` libraries, we suggest using the `hunspell` and `pyhunspell` libraries instead in the `util.py`:
```
pip install hunspell == 0.5.5
sudo apt install hunspell-en-gb hunspell-en-us
```
```
import hunspell

uk_dict = hunspell.HunSpell('/usr/share/hunspell/en_GB.dic', '/usr/share/hunspell/en_GB.aff')
us_dict = hunspell.HunSpell('/usr/share/hunspell/en_US.dic', '/usr/share/hunspell/en_US.aff')

def change_british_to_american(word):
    if uk_dict.spell(word) and not us_dict.spell(word):
        suggestions = us_dict.suggest(word)
        return suggestions[0] if suggestions else word
    return word
```

### 4. Install Ollama:
- GitHub link: https://github.com/ollama/ollama
  - Install Ollama: https://ollama.com/download
  - Ollama FAQs: https://github.com/ollama/ollama/blob/main/docs/faq.md
  - Link Ollama to LangChain: https://python.langchain.com/v0.1/docs/integrations/llms/ollama/
- Install PyTorch: https://pytorch.org/get-started/locally/
- Install Open WebUI: https://docs.openwebui.com/getting-started/ (optional for GUI access to LLMs)
- Install Ollama on Ubuntu and CUDA 12.2:
  - Install or update Ollama:
  ```
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  - Start or stop Ollama in the process:
  ```
  sudo systemctl start ollama
  sudo systemctl stop ollama
  ```
  - Install PyTorch:
  ```
  pip3 install torch torchvision torchaudio
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
  ollama list | awk 'NR>1 {print $1}' | xargs -I {} sh -c 'echo "Updating model: {}"; ollama pull {}; echo "--"' && echo "All models updated."
  ```
  Please check this link for further updates: https://github.com/ollama/ollama/issues/2633

### 5. Setup Large Language Models (LLMs):

At present, multiple LLM models are used in the experiments. The reader is referred to README.md for models currently used and reference therein to the API access or download, pricing, and licensing for each model.

- You will need API keys to interact with API-accessed commercial LLMs.
  - OpenAI: https://platform.openai.com/account/api-keys
  - Anthropic: https://console.anthropic.com/settings/keys
- Create a file named as `.env` and write:
```
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
ANTHROPIC_API_KEY = <YOUR_ANTHROPIC_API_KEY>
```
- To protect your API keys, please add `.env` into the file `.gitignore`:
```
.env
```
```
git rm --cached .env
```
- Load API keys into the file `run_config.py`:
```
import os
import dotenv

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
```
- Select one LLM in the file `run_config.py`:
```
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

# load GPT models: https://platform.openai.com/docs/models/
# pricing: https://openai.com/api/pricing/
llm = ChatOpenAI(model_name='gpt-4o-2024-05-13', temperature=0)
llm = ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0)
llm = ChatOpenAI(model_name='gpt-3.5-turbo-0125', temperature=0) # old, not included

# load Anthropic models: https://docs.anthropic.com/en/docs/about-claude/models
# pricing: https://www.anthropic.com/pricing#anthropic-api
llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0) # expensive, not included
llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

# load Llama models
llm = ChatOllama(model="llama3:8b", temperature=0)
llm = ChatOllama(model="llama3.1:8b", temperature=0)

# load Qwen models
llm = ChatOllama(model="qwen2:7b", temperature=0)
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

# load Gemma models
llm = ChatOllama(model="gemma2:9b", temperature=0)

# load GLM models
llm = ChatOllama(model="glm4:9b", temperature=0)
```
- Select one embeddings service in the file `run_config.py`:
```
# https://platform.openai.com/docs/guides/embeddings/embedding-models
embeddings_service = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_length = 1536
embeddings_service = OpenAIEmbeddings(model="text-embedding-3-small")
vector_length = 1536
embeddings_service = OpenAIEmbeddings(model="text-embedding-3-large")
vector_length = 3072
```
**Author Note**
- It is possible to use embedding models other than OpenAI. For example, the following works for Llama 3 embedding models:
```
pip install langchain-ollama == 0.2.2
```
```
from langchain_ollama import OllamaEmbeddings

embeddings_service = OllamaEmbeddings(model="llama3:8b")
vector_length = 4096
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
- The alignment result will be stored in the folder `alignment/`.
- The performance evaluation will be stored in the file `result.csv`.
- The cost evaluation will be stored in the file `cost.csv`.
- The matching log will be stored in the file `agent.log`.

## Repository Structure:

### 1. Data:
- `data/`: data from three OAEI tracks.

### 2. Experiments:
- `alignment/`: alignment results.
- `om_ontology_to_csv.py`: Retrieval Agent Part 1.
- `om_csv_to_database.py`: Retrieval Agent Part 2.
- `om_database_matching.py`: Matching Agent.
- `run_config.py`: main function of the project.
- `run_series_conference.py`: run all the conference alignments at one time.
- `run_series_similarity.py`: run different similarity thresholds for one alignment at one time.
- `llm_matching.py`: examples using purely LLMs for general matching tasks.
- `llm_om_only.py`: examples of using LLMs only for ontology matching.
- `llm_om_with_context.py`: examples of using LLMs with context information for ontology matching.
- `util.py`: util component of the project.

Frequently Asked Questions (FAQs):
- Why does the Retrieval Agent have two parts `om_ontology_to_csv.py` and `om_csv_to_database.py`?  
Answer: You can simply combine these two parts together. We decompose this into two parts to make it easy to debug any issues that may occur in the database storage.

- Why `om_csv_to_database.py` create three additional columns `syntactic_matching`, `lexical_matching`, and `semantic_matching` in the table `ontology_matching`?  
Answer: You can simply ignore these columns. We add these columns to debug any issues that may occur in the database storage.

- Why do I find a slight difference for each run?  
Answer: It is because https://community.openai.com/t/run-same-query-many-times-different-results/140588

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
- `generate_anatomy_mse_benchmark.py`: generate the results of OAEI Anatomy Track and MSE Track.
- `fix_inconsistent_reference.py`: fix the URI issue of OAEI tracks.
- `benchmark_2022/`: results of OAEI 2022.
- `benchmark_2023/`: results of OAEI 2023.

### 4. Visualisation:
- `draw_benchmark.ipynb`: visualise the results of the evaluation.
- `draw_ablation_study.ipynb`: visualise the results of the ablation study.
- `result_csv/`: original data of the results.
- `result_figure/`: visualisation of the results.
- Our visualisation is inspired by the following references:
  - https://joernhees.de/blog/2010/07/22/precision-recall-diagrams-including-fmeasure/
  - https://towardsai.net/p/l/precision-recall-curve

## Debugging Log:
- We have created a debugging log for this project. [Click the link here.](DEBUGGING_LOG.md)

## Ethical Considerations:
- AI-generated content (AIGC) is labelled as "AI-generated content". AIGC can contain harmful, unethical, prejudiced, or negative content (https://docs.mistral.ai/capabilities/guardrailing/). However, ontology matching tasks only check the meaning of domain-specific terminologies, and we have not observed such content being generated.

### Code Acknowledgements:
- Our data-driven application architecture is inspired by: https://colab.research.google.com/github/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/postgres/pgvector/notebooks/pgvector_gen_ai_demo.ipynb

### License:

<!-- Which licence is best for your work? Check with the CC License chooser: https://chooser-beta.creativecommons.org/ -->

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
