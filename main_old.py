import logging
import os
import base64
import json
from typing import List

from logging import config
from dotenv import load_dotenv
from log_config import logging_config
import streamlit as st
from weaviatedb import WeaviateClient
from scryfallapi import ScryfallClient
from scryfallapi import Card

load_dotenv()  # take environment variables from .env.
config.dictConfig(logging_config)  # Load the logging configuration

WEAVIATE_CLASS = "MTGCard"
SETS = ['ltc', 'mkm', 'unf', 'woe']
IMG_PATH = "../ImageFolder"
META_PATH = '../CardMetadata'


#"moduleConfig": {
#  "multi2vec-clip": {
#    "imageFields": [
#      "image"
#    ]
#  }
#},
#"vectorizer": "multi2vec-clip",

run_logging = logging.getLogger("runner")  # initialize the main logger


def load_weaviate_schema(client: WeaviateClient, schema_path: str) -> None:
    """
    Creates the schema in Weaviate for the configured class. The schema is removed first if it already exists.
    """
    if client.does_class_exist(WEAVIATE_CLASS):
        client.delete_class(WEAVIATE_CLASS)
        run_logging.info("Removed the existing Weaviate schema.")

    client.create_classes(path_to_schema=schema_path)
    run_logging.info("New schema loaded for class '%s'.", WEAVIATE_CLASS)


# def store_images(client: WeaviateClient) -> None:
#     """
#     Reads all jpg files from the configured img path. Each file is converted into a base64 encoded string. Next it
#     is stored into Weaviate using the batch interface.

#     :param client: Client for interacting with Weaviate
#     :return: Nothing
#     """
#     with client.client.batch(batch_size=5) as batch:
#         for file_name in os.listdir(IMG_PATH):
#             for file_name in os.listdir(IMG_PATH):
#                 if file_name.endswith(".jpg"):
#                     with open(IMG_PATH + file_name, "rb") as img_file:
#                         b64_string = base64.b64encode(img_file.read())

#                     data_obj = {"filename": file_name, "image": b64_string.decode('utf-8')}
#                     batch.add_data_object(data_obj, WEAVIATE_CLASS)
#                     run_logging.info("Stored file: %s", file_name)

def get_card_data(metadata:str):
    if 'card_faces' in metadata:
        combined_oracle_text = ""
        for card_face in metadata['card_faces']:
            combined_oracle_text += card_face["oracle_text"] + " "
        oracle_text = combined_oracle_text
    else:
        oracle_text = metadata['oracle_text']
    return {
            "card_name": metadata['name'],
            "colors": ','.join(metadata['colors']),
            "oracle_text": oracle_text,
            "type_line": metadata['type_line'],
            "set_id": metadata['set'],
            "image_url": metadata['image_uris']['normal']
            }




def store_images_data(client: WeaviateClient) -> None:

    with client.client.batch(batch_size=5) as batch:
        for edition in SETS:
            full_img_path = f'''{IMG_PATH}/{edition}/'''
            full_meta_path = f'''{META_PATH}/{edition}/'''
            for img_name in os.listdir(full_img_path):
                for data_name in os.listdir(full_meta_path):
                    
                    if os.path.splitext(os.path.basename(img_name))[0] == os.path.splitext(os.path.basename(data_name))[0]:
                        if img_name.endswith(".jpg"):
                            with open(full_meta_path + data_name, "rb") as meta_file:
                                meta_data = json.load(meta_file)
                            with open(full_img_path + img_name, "rb") as img_file:
                                b64_string = base64.b64encode(img_file.read())

                            data_obj = get_card_data(meta_data)
                            data_obj["filename"] = img_name
                            data_obj["image"] = b64_string.decode('utf-8')
                            batch.add_data_object(data_obj, WEAVIATE_CLASS)
                            run_logging.info("Stored file: %s", img_name)

def store_cards_metadata(client: WeaviateClient) -> None:
    """
    Reads all jpg files from the configured img path. Each file is converted into a base64 encoded string. Next it
    is stored into Weaviate using the batch interface.

    :param client: Client for interacting with Weaviate
    :return: Nothing
    """
    with client.client.batch(batch_size=5) as batch:
        for set in SETS[0:1]:
            full_meta_path = f'''{META_PATH}/{set}/'''
            for data_name in os.listdir(full_meta_path):                    
                with open(full_meta_path + data_name, "rb") as meta_file:
                    meta_data = json.load(meta_file)

                data_obj = get_card_data(meta_data)
                data_obj["filename"] = data_name
                batch.add_data_object(data_obj, WEAVIATE_CLASS)
                run_logging.info("Stored file: %s", data_name)


def store_cards(client: WeaviateClient, cards: List[Card]) -> None: 

    return 

# def query_from_text(client: WeaviateClient, query_text: str, the_limit: int = 3):
#     run_logging.info("Executing the query '%s'", query_text)
#     near_text = {"concepts": [query_text]}
    
#     response = (client.client.query
#                    .get(WEAVIATE_CLASS, ["filename",
#                                           "card_name",
#                                           "type_line",
#                                           "colors",
#                                           "set_id",
#                                           "image_url", 
#                                           "oracle_text"
#                                           ])
#                    .with_near_text(near_text)
#                    .with_limit(the_limit)
#                    .with_additional(properties=["certainty", "distance"])
#                    .do())
#     if response["data"]["Get"][WEAVIATE_CLASS]:
#         found_picts = response["data"]["Get"][WEAVIATE_CLASS]
#         print(found_picts)
#         return [{"filename": pict["filename"], 
#                  "card_name": pict['card_name'],
#                  "set_id": pict['set_id'],
#                  "image_url": pict['image_url'],
#                  "certainty": pict["_additional"]["certainty"]} for pict in found_picts]

#     return []


def query_similar_images(client: WeaviateClient, query_text: str, the_limit: int = 3):
    """
    Queries weaviate for available images that match the provided search terms.
    :param client: Client for interacting with Weaviate
    :param query_text: Provided image for matching similar images
    :param the_limit: Number of images to return, defaults to 3
    :return: List of objects with properties filename and certainty
    """
    run_logging.info("Executing the query '%s'", query_text)
    sourceImage = { "image": query_text}

    response = (client.client.query
                   .get(WEAVIATE_CLASS, ["filename", "card_name"])
                   .with_near_image(sourceImage, encode=False)
                   .with_limit(the_limit)
                   .with_additional(properties=["certainty", "distance"])
                   .do())
    if response["data"]["Get"][WEAVIATE_CLASS]:
        found_picts = response["data"]["Get"][WEAVIATE_CLASS]
        return [{"filename": pict["filename"], 
                 "card_name": pict['card_name'],
                 "set": pict['set'],
                 "image": pict['image'],
                 "certainty": pict["_additional"]["certainty"]} for pict in found_picts]

    return []

def reload_data(client: WeaviateClient) -> None:
    """
    Loads a fresh instance of the Cards schema, removes the old one if present.
    :param client: Client for interacting with Weaviate
    :return: Nothing
    """
    load_weaviate_schema(client=client, schema_path="./config_files/weaviate_clip.json")
    # store_images(client)
    store_images_data(client)
    # store_cards_metadata(client)
    # store_cards(client)


def get_cards_from_api(client:ScryfallClient, set_code:str):
    set_cards = client.get_entire_set(set_code)
    
    for card in set_cards:
        print(card.get_card_name())



@st.cache_resource
def create_weaviate_client(url: str = None):
    """
    Utility method to make it possible for Streamlit to cache the Weaviate client access.
    :param url: String containing the url for the Weaviate cluster
    :return: The created WeaviateClient instance
    """
    return WeaviateClient(overrule_weaviate_url=url)

@st.cache_resource
def create_scryfall_client(url: str = None):
    return ScryfallClient()

def print_results(cols, picts):
    for col, picture in zip(cols, picts):
        print(picture)
        filename = picture["filename"]
        card_name = picture["card_name"]
        certainty = picture["certainty"]
        set_id = picture["set_id"]
        image_url = picture["image_url"]

        with col.container():
            col.image(image=image_url,
                        caption=card_name,
                        width=200)
            col.write(f"certainty: {'{:.5f}'.format(certainty)}")

if __name__ == '__main__':
    weaviate_client = create_weaviate_client(url="http://localhost:8080")
    scryfall_client = create_scryfall_client()
    st.title("Search for Cards")

    st.sidebar.button(label="Reload data",
                      key="reload_data",
                      on_click=reload_data,
                      kwargs={"client": weaviate_client})
    
    st.sidebar.button(label="load from API",
                      key="reload_api",
                      on_click=get_cards_from_api,
                      kwargs={"client": scryfall_client})

    # Initialize the table for Streamlit with a specified number of rows and the maximum number of images
    n_cols = 3
    n_picts = 6

    n_rows = int(1 + n_picts // n_cols)

    the_query = st.text_input('Describe card in one or a few words')
    # scryfall_search = st.text_input('Search in Scryfall')
    uploaded_file = st.file_uploader(label='Upload file :sunglasses:', type=['png','jpg'])

    rows = [st.columns(n_cols) for _ in range(n_rows)]
    cols = [column for row in rows for column in row]

    # Execute the query if there is text in the query box
    # if uploaded_file:
    #     the_query=''
    #     img_str = base64.b64encode(uploaded_file.getvalue()).decode()
    #     picts = query_similar_images(client=weaviate_client, query_text=img_str, the_limit=n_picts)
    #     st.sidebar.image(image =uploaded_file.getvalue())
    #     print_results(cols, picts)


    # if the_query:
    #     img_str=''
    #     picts = query_from_text(client=weaviate_client, query_text=the_query, the_limit=n_picts)
    #     print_results(cols, picts)
