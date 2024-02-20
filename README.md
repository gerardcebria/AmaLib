# AmaLib
Reads and answer questions about the CVs stored on the project folder. 

## Install requirements 
use the command line

`pip install -r requirements.txt`

## Weaviate
You will need an OpenAI key to configure the Weaviate Server.

To run the Weaviate server use the command: 

`docker compose -f infra/docker-compose-weaviate-openai.yml up -d`


## App - Streamlit
To run the streamlit app run:

`steamlit run main.py`

## Basic Run
 1. Put the CVs (resumes) on the root, under a folder named `data_source`
 2. On the app, running in `http://localhost:8501/`, press the `Reload data` button
 3. Ask que question on the input text