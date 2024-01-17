### IMPORTANT NOTICE:  
(1) Do not share, because OPENAI API is exposed in multi_vectorstore_with_openai.ipynb and multi_vectorstore_with_openai-OM.ipynb  
(2) Call Huanyu for approval for trivial reference

### Run All: `python run_config.py`  
(1) om_ontology_to_csv.py  
(2) om_csv_to_database.py  
(3) om_database_matching.py  

### Benchmark:  
(1) conference: `python generate_conference_benchmark.py`  
(2) anatomy & mse: `python generate_other_benchmark.py` 

### Visualisation: `python draw_recall_precision.py`  
(1) https://joernhees.de/blog/2010/07/22/precision-recall-diagrams-including-fmeasure/  
(2) https://towardsai.net/p/l/precision-recall-curve  

### Install Packages:  
(1) pip install pandas  
(2) pip install langchain[all]  
(3) pip install openai  
(4) pip install rdflib  
(5) pip install sentence-transformers   
(6) pip install python-dotenv  
(7) pip install pyenchant  
(8) pip install tiktoken  
(9) pip install google-api-python-client  
(10) pip install wikipedia  
(11) pip install faiss-gpu  
(12) pip install deeponto  
(13) pip install pypdf

### Install Database:  
(1) psql –version  
(2) sudo -u postgres psql  
(3) alter user postgres password 'postgres'  
(4) sudo apt install postgresql-15-pgvector  
Example: https://colab.research.google.com/github/GoogleCloudPlatform/python-docs-samples/blob/main/cloud-sql/postgres/pgvector/notebooks/pgvector_gen_ai_demo.ipynb  

### Other Useful Links:  
https://github.com/kyrolabs/awesome-langchain  
https://python.langchain.com/docs/integrations/vectorstores/faiss  
https://github.com/insightbuilder/python_de_learners_data/blob/main/code_script_notebooks/projects/LLM_practical_appln/multiFileEmbedFaiss.ipynb  
https://github.com/samwit/langchain-tutorials/blob/main/YT_Chat_your_PDFs_Langchain_Template_for_creating.ipynb  
https://www.kaggle.com/code/harpdeci/retrieval-augmented-generation-in-langchain  
https://towardsdatascience.com/billion-scale-semantic-similarity-search-with-faiss-sbert-c845614962e2  
https://github.com/UKPLab/plms-graph2text  
https://github.com/rikdz/GraphWriter  
https://github.com/thu-coai/JointGT  
https://github.com/acolas1/GAP_COLING2022  
http://attempto.ifi.uzh.ch/site/docs/writing_owl_in_ace.html  
https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/07-langchain-tools.ipynb  