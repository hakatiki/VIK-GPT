import streamlit as st
import json
from tad import tad_process 
from tvsz import tvsz_process
import time
from datetime import datetime
from qa_v2 import solr_retrieve, embedding_retrieve, get_solr_url

import streamlit as st

def run_query_app():
    st.title("Query the database")
    pipeline = st.selectbox(
        "Select Pipeline:",
        ["Solr", "Embedding"],
        index=0  # Default to TAD
    )
    query = st.text_input("Query", "Hány éves a BME?")
    if st.button("Excecute query"):
        if pipeline == "Solr":
            try:
                tmp = solr_retrieve(query)
                result = tmp[0]['page_content_t']
            # query = st.text_input("Query", "Hány éves a BME?")
            except Exception:
                # result = tmp
                result = get_solr_url()
        elif pipeline == "Embedding":
            result = embedding_retrieve(query)[0]['page_content_t']
        st.text_area(label="Result", value=result, height=800)