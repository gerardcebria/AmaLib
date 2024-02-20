import weaviate
from weaviate.embedded import EmbeddedOptions
from pypdf import PdfReader
from weaviatedb import WeaviateClient
from pathlib import Path
import os

import logging
from logging import config
from log_config import logging_config

config.dictConfig(logging_config)
run_logging = logging.getLogger("runner")

folder_path = "./data_source"
schema_path = './config_files/weaviate_openai.json'
WEAVIATE_CLASS = 'Resume'

def read_pdf(pdf_file):
    pdf_path = os.path.join(folder_path, pdf_file)
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return {
            'source': os.path.splitext(pdf_file)[0],
            'facts': text 
        }


def extract_data(folder_path:str):
    files = []
    for pdf_file in os.listdir(folder_path):
        if pdf_file.endswith(".pdf"):
            files.append(read_pdf(pdf_file))
            print(f"Text extracted from {pdf_file}:")
    return files


def load_files(client: WeaviateClient, folder_path:str):
    if client.does_class_exist(WEAVIATE_CLASS):
        client.delete_class(WEAVIATE_CLASS)
        run_logging.info("Removed the existing Weaviate schema.")
    client.create_classes(path_to_schema=schema_path)
    run_logging.info("New schema loaded for class '%s'.", WEAVIATE_CLASS)
    files = extract_data(folder_path)
    for pdf_file in files:
        with client.client.batch(batch_size=5) as batch:
            batch.add_data_object(pdf_file, WEAVIATE_CLASS)
            run_logging.info("Stored file: %s", pdf_file['source'])
        
