import logging
import os
from pprint import pprint

import jq
import pandas as pd
import weaviate
# from bs4 import BeautifulSoup
from dotenv import load_dotenv

from util import load_json_body_from_file

load_dotenv()  # take environment variables from .env.

auth_config = weaviate.auth.AuthApiKey(
    api_key=os.getenv('WEAVIATE_API_KEY'),
)


class WeaviateClient:
    def __init__(self, overrule_weaviate_url: str = None):
        if overrule_weaviate_url:
            weaviate_url = overrule_weaviate_url
        else:
            weaviate_url = os.getenv('WEAVIATE_URL')

        self.logger = logging.getLogger("weaviate")
        self.logger.info("Creating a new WeaviateClient")

        if weaviate_url is None:
            self.logger.error("Cannot create a Weaviate instance with an empty URL")

        if not weaviate_url.startswith("http://localhost"):
            self.client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=auth_config,
                additional_headers={
                    "X-OpenAI-Api-Key": os.getenv('OPEN_AI_API_KEY')
                }
            )
        else:
            self.client = weaviate.Client(
                url=weaviate_url,
            )

        self.logger.info(f"Weaviate client is connected: {self.client.is_ready()}")

    def __del__(self):
        self.logger.debug("Removing the WeaviateClient from the earth")

    def inspect(self):
        pprint(self.get_schema())
        pprint(self.client.get_meta())
        pprint(self.find_classes())

    def get_schema(self):
        return self.client.schema.get()

    def create_classes(self, path_to_schema: str):
        class_obj = load_json_body_from_file(file_name=path_to_schema)

        self.client.schema.create_class(class_obj)

    def delete_schema(self):
        self.client.schema.delete_all()

    def delete_class(self, class_name: str):
        self.client.schema.delete_class(class_name)

    def does_class_exist(self, class_name: str) -> bool:
        return self.client.schema.exists(class_name)

    def find_classes(self):
        schema = self.client.schema.get()
        return jq.compile(".classes[].class").input(schema).all()

    def load_data(self):
        url = 'https://raw.githubusercontent.com/weaviate/ref2vec-ecommerce-demo/main/weaviate-init/metadata/metadata' \
              '/products_gear_bags.csv'
        df = pd.read_csv(url, encoding='utf-8')

        # Configure a batch process
        with self.client.batch as batch:
            batch.batch_size = 100
            # Batch import all Questions
            for index, row in df.iterrows():
                self.logger.info(f"importing question")

                properties = {
                    "category": self.__clean_html(row["category"]),
                    "name": self.__clean_html(row["name"]),
                    "price": row["price"],
                    "qty": row["qty"],
                    "description": self.__clean_html(row["description"])
                }

                self.client.batch.add_data_object(properties, "Product")

    @staticmethod
    def __clean_html(to_clean: str):
        """
        Removes all HTML tags from the provided text and returned the cleaned text
        :param to_clean: String containing the text to be cleaned
        :return: The cleaned string
        """
        soup = BeautifulSoup(to_clean, 'html.parser')
        no_html = soup.get_text()
        return no_html.replace("\n", " ")

    def query(self, query_text: str):
        near_text = {"concepts": [query_text]}

        return (
            self.client.query
            .get("Product", ["name", "description", "category"])
            .with_near_text(near_text)
            .with_limit(5)
            .do()
        )
