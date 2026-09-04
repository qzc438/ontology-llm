## Agent-OM: Leveraging LLM Agents for Ontology Matching
- The preprint of the paper is available at arXiv: https://arxiv.org/abs/2312.00326
- The source code, data, and/or other artifacts are available at GitHub: https://github.com/qzc438/ontology-llm

## News:
- This paper has been accepted by PVLDB 2025: https://www.vldb.org/pvldb/volumes/18/paper/Agent-OM%3A%20Leveraging%20LLM%20Agents%20for%20Ontology%20Matching
- The slide presentation of the PVLDB 2025 paper can be found in the `slide_presentation` folder.
- A production version linked to the PVLDB 2025 paper can be found in the `Releases` section.
```bibtex
@article{qiang2023agent,
    title={{Agent-OM}: Leveraging {LLM} Agents for Ontology Matching},
    author={Zhangcheng Qiang and Weiqing Wang and Kerry Taylor},
    journal={Proceedings of the {VLDB} Endowment},
    year={2024},
    volume={18},
    number={3},
    pages={516--529},
    address={London, UK},
    publisher={VLDB Endowment},
    doi={10.14778/3712221.3712222}
}
```

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
- **That is all you create.** The database has to exist and be empty; the tables
  are not yours to make. `om_csv_to_database.py` runs
  `CREATE EXTENSION IF NOT EXISTS vector` itself, and it drops and recreates its
  four tables at the start of every run: `ontology_matching`,
  `syntactic_matching`, `lexical_matching` and `semantic_matching`. Do not
  create them by hand, and do not keep anything else in this database, since a
  run will drop those four tables whatever is in them.
- pgvector still has to be **installed on the PostgreSQL server**, even though
  the run enables it: `CREATE EXTENSION` can only switch on an extension that is
  already present. Without it a run stops at
  `ERROR: extension "vector" is not available`, whose own hint is that the
  extension must first be installed on the system where PostgreSQL is running.
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
- Alternatively, you can run the following script to install all required packages:
```
pip install -r requirements.txt
```
- Deal with the blank page: https://stackoverflow.com/questions/55152948/juypter-notebook-shows-blank-page

**Author Note**: There is a known issue with the `Enchant` and `PyEnchant` libraries, we suggest using the `hunspell` and `pyhunspell` libraries instead in the `util.py`.
```
sudo apt update
sudo apt install -y build-essential pkg-config libhunspell-dev hunspell
sudo apt install hunspell-en-gb hunspell-en-us
pip install hunspell==0.5.5
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
**Author Note**: To ensure consistency and reproducibility, we recommend using API-accessed models with a timestamp tag.
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
- It is possible to use embedding models other than OpenAI. For example, the following works for Llama 3 embedding models.
```
pip install langchain-ollama==0.1.0
```
```
from langchain_ollama import OllamaEmbeddings

embeddings_service = OllamaEmbeddings(model="llama3:8b")
vector_length = 4096
```
**Author Note**: The current setting of Agent-OM for the OAEI 2025 campaign are as follows.
- Agent-OM (Product Version):
```
llm = ChatOpenAI(model_name='gpt-4o-2024-05-13', temperature=0.0, seed=42, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0)
embeddings_service = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_length = 1536
```
- Agent-OM-Lite (Lightweight Version):
```
llm = ChatOllama(model="llama3:8b", temperature=0.0, seed=42, top_p=1.0, top_k=1, repeat_penalty=1.0)
embeddings_service = OllamaEmbeddings(model="llama3:8b")
vector_length = 4096
```

### 6. Setup Matching Task:
- To ensure all the data uses the consistent reference schema, please run the following code:
```
python fix_inconsistent_reference.py
```
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
The same pipeline, three ways to start it. They produce the same results and read the same `run_config.py`; they differ in how much you set up by hand.

#### (1) Run on Local Machine
- Run the script:
```
python run_config.py
```
- The alignment result will be stored in the folder `alignment/`. You can run the script `csv_to_alignment_api.py` to convert the CSV format to Alignment API format: https://moex.gitlabpages.inria.fr/alignapi/format.html
- The performance evaluation will be stored in the file `result.csv`. The first five lines are the intermediate results for debugging purposes. For the final result, you should use the last line that ends with "llm_with_agent".
- The cost evaluation will be stored in the file `cost.csv`. The cost calculation only works for API-accessed commercial LLMs.
- The time evaluation will be stored in the file `time.csv`. The unit of measurement is milliseconds.
- The matching log will be stored in the file `agent.log`. This file will be rewritten when you run a new task.

#### (2) Run on Web Interface
Instead of editing `run_config.py` by hand, you can upload a pair of ontologies from a web page and watch the run happen.
```
python web_app.py
```
Open http://127.0.0.1:5000 and work down the three cards. **Start matching** sits below all three, because it needs all three.

1. **Input Files.** Name the source and target ontologies, choose their files (`.xml`, `.rdf` or `.owl`), then click **Upload**. Choosing a file only names it on the page; nothing is sent until you press Upload. Both names are required, because they are what the run is filed under. A reference alignment is optional: without one the run still matches the two ontologies, but there is nothing to score it against, so it produces no precision, recall or F1.
2. **Environment Variables.** Check that the database and the other lines are green, and that both API keys are set. A key that is not in `.env` can be typed in here.
3. **Matching Settings.** Choose the LLM, the embedding model, the context and the thresholds for this run. Anything you leave alone keeps the value already written in `run_config.py`.

Then press **Start matching**. The terminal output of `run_config.py` streams to the page while it runs. When it finishes the page shows the precision, recall and F1 of the `llm_with_agent` stage, with the earlier stages underneath, and every file the run produced is listed for download: "Original Files" for what the matching wrote, "Scoring Files" for `result.csv`, `time.csv` and `cost.csv`.

**Where the files go.** A run is filed the way the OAEI tracks are, `<context>/<source>-<target>-<timestamp>`. Naming the ontologies `cmt` and `confof` with the context `conference` files the run as `conference/cmt-confof-20260827-163210`:

```
Uploads     data/uploads/conference/cmt-confof-20260827-163210/component/
Results     alignment/uploads/conference/cmt-confof-20260827-163210/component/
```

Everything stays under `uploads/`, so a web run can never overwrite the OAEI data in `data/` or the reference results in `alignment/`, and the timestamp keeps every run of a pair rather than replacing the one before it. Each run also writes its own `result.csv`, `cost.csv` and `time.csv` into its own folder, so its scores are not mixed in with every other run's.

**Worth knowing**
- **One run at a time.** The pipeline writes to a single database and to shared CSV files, so a second run is refused while one is in progress.
- **Do not delete a run's folders while it is running.** It reads the uploads throughout.
- **The keys are readable by anyone who can open the page.** They are held in memory for the session, or written to `.env` if you tick "also save to .env". This is why the server listens on `127.0.0.1` and has no login. `--port 8080` picks another port and `--host 0.0.0.0` exposes it to the network, which you should only do on a network you trust completely.
- **Restart after editing `web_app.py` or `web_overrides.py`.** Python reads both once, at start-up. The Server line turns red when either has changed since. The page and the stylesheet reload on their own.
- **Day and night modes.** The page follows the clock on your machine, night from 18.00 to 06.00, and the symbol in the top right overrides it: one button cycling automatic, day and night. The design notes are at http://127.0.0.1:5000/design-system.
- **`run_config.py` is never written to.** The chosen settings travel to the pipeline in an environment variable and are applied while it runs, so `python run_config.py` from the terminal behaves exactly as it did before.

#### (3) Run on Docker
The same web interface, with the database and an Ollama for the open models brought up beside it. You need Docker with the Compose plugin, and the `.env` file from step 5 beside `docker-compose.yml`.
```
./start.sh --build
```
Then open http://127.0.0.1:5000. `start.sh` uses an NVIDIA GPU if the machine has one and the CPU if it does not; `docker compose up --build` also works and never looks for a GPU.
- **Nothing from steps 1 to 4 is needed on your machine for this.** No
  PostgreSQL, no pgvector, no `ontology` database, no virtual environment, no
  Ollama. Compose runs PostgreSQL 16 with pgvector as its own `db` container and
  Ollama as its own `ollama` container, and the web container reaches them by
  name. The database lives in a Docker volume, `db-data`, not on your machine
  and not inside the image, so it survives `docker compose down` and is
  discarded only by `docker compose down -v`. All you provide is Docker itself
  and the `.env` file from step 5 holding your API keys.
- Ollama is not built into the image: compose fetches the official `ollama/ollama` image on the first start and runs it as a service, so the open models work without anything on the host. Choose one and press **Download** beside it to pull it, which happens in that service and is kept in the `ollama-models` volume. It runs on the CPU unless the machine has an NVIDIA card, in which case `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d` hands the GPU over, needing the NVIDIA container toolkit but no editing; to use the Ollama already on your machine instead, which is faster when it has the GPU and the models, start with `OLLAMA_URL=http://host.docker.internal:11434 docker compose up` and see the open models section of [DOCKER.md](DOCKER.md), since it also has to listen on more than `127.0.0.1`.
- **[DOCKER.md](DOCKER.md) is the full guide**: settings, where your files go, everyday commands, troubleshooting, and why it is put together the way it is.

**In summary**

| | Set up on your machine | Settings chosen by |
| --- | --- | --- |
| (1) Local machine | steps 1-4 | editing `run_config.py` |
| (2) Web interface | steps 1-4 | the page |
| (3) Docker | Docker only | the page |

## Repository Structure:

### 1. Data:
- `data/`: data from OAEI tracks.
- `find_data_vocabulary.py`: summarise the vocabulary used in OAEI tracks.
- `find_reference_only.py`: find the reference alignment only.
- `fix_inconsistent_reference.py`: fix the URI issue of OAEI tracks.

### 2. Experiments:
- `alignment/`: alignment results.
- `om_ontology_to_csv.py`: Retrieval Agent Part 1.
- `om_csv_to_database.py`: Retrieval Agent Part 2.
- `om_database_matching.py`: Matching Agent.
- `run_config.py`: main function of the project.
- `web_app.py`: web interface to upload a pair of ontologies and run `run_config.py` from the browser.
- `web_overrides.py`: reads the settings and their alternatives out of `run_config.py`, and applies the ones chosen in the web interface without editing the file.
- `templates/index.html`: the page served by `web_app.py`.
- `templates/design_system.html`: the Design System notes, served at `/design-system`.
- `static/anu.css`: the Design System stylesheet, derived from the ANU Web Style Guide.
- `static/theme.js`: chooses the day or night mode and remembers the reader's override.
- `Dockerfile`, `docker-compose.yml`, `docker/init-pgvector.sql`: run the web interface and its database in containers.
- `DOCKER.md`: the guide to running it that way.
- `run_series_archaeology.py`: run all the archaeology alignments at one time.
- `run_series_conference.py`: run all the conference alignments at one time.
- `run_series_multifarm.py`: run all the multifarm alignments at one time.
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

- How do I use the file `run_series_archaeology.py` and `run_series_conference.py`, and `run_series_multifarm.py`?  
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

### 5. Competitions and Challenges:
- `campaign/OAEI_2025`: results of OAEI 2025 campaign.

## Debugging Log:
- We have created a debugging log for this project. [Click the link here.](DEBUGGING_LOG.md)

## Ethical Considerations:
- AI-generated content (AIGC) can contain harmful, unethical, prejudiced, or negative content (https://docs.mistral.ai/capabilities/guardrailing/). However, ontology matching tasks only check the meaning of domain-specific terminologies, and we have not observed such content being generated.

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