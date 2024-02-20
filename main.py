import streamlit as st
from weaviatedb import WeaviateClient
from pdflib import extract_data, load_files

folder_path = "./data_source"


pdf_text = extract_data(folder_path)

@st.cache_resource
def create_weaviate_client(url: str = None):
    """
    Utility method to make it possible for Streamlit to cache the Weaviate client access.
    :param url: String containing the url for the Weaviate cluster
    :return: The created WeaviateClient instance
    """
    return WeaviateClient(overrule_weaviate_url=url)


def query_cv(query_text:str, client:WeaviateClient):
    prompt = '''You are a human resources assistant. Your task will be to process resumes and provide information about those resumes when requested.
                The resumes belong to developers, so they include keywords such as frontend, backend, AWS, Azure, etc.
                Try to extract the key words to be able to respond to questions asked by recruiters. User your own knowledge. 
                For example:
                If the recruiter asks you: Does this programmer know how to program in JavaScript?
                And you see that in the resume the programmer knows Angular, which is a JavaScript framework, then they will likely know JavaScript.
            '''
    ask = {
        "question": f'''{prompt}
                    So if I ask you the following question {query_text}
                    you respond:''',
        "properties": ["facts"]
    }
    response = (client.client.query
                    .get("Resume", ["source", "_additional {answer {hasAnswer property result startPosition endPosition} }"])
                    .with_ask(ask)
                    .with_limit(1)
                    .do()
                    )
    return response

if __name__ == '__main__':
    weaviate_client = create_weaviate_client(url="http://localhost:8080")
    cv_processed = ''
    
    st.title("Search for CVs")

    data_loaded = st.sidebar.button(label="Reload data",
                      key="reload_data",
                      on_click=load_files,
                      kwargs={"folder_path":folder_path,
                              "client": weaviate_client})
    
    the_query = st.text_input('Ask a question about our profiles')

    if the_query:
        response = query_cv(query_text=the_query, client=weaviate_client)

        result = response['data']['Get']['Resume'][0]['_additional']['answer']['result']
        source = response['data']['Get']['Resume'][0]['source']        

        st.text_area(label="Answer", value=f'''{result} (source: {source}.pdf)''')
        st.text_area(label="complete", value=response)
        
