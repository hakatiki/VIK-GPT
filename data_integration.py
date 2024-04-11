import streamlit as st
import json
from tad import tad_process 
from tvsz import tvsz_process
import time
from datetime import datetime

import streamlit as st

def run_data_app():
    st.title("Text or URL Processing")

    # Pipeline selection
    pipeline = st.selectbox(
        "Select Pipeline:",
        ["TAD", "TVSZ"],
        index=0  # Default to TAD
    )

    if pipeline == "TAD":
        st.subheader("TAD Configuration")
        model_name = st.text_input("Model Name:", "text-embedding-3-large")
        url = st.text_input("URL:", "https://portal.vik.bme.hu/kepzes/targyak/?order=s.code&own=&department_id=all&has_datasheet=all&active=1&program=all")
        base_url = st.text_input("Base URL:", "https://portal.vik.bme.hu")
        save_path = st.text_input("Save Path:", "../documents/tad/tad.json")
        tad_faiss_path = st.text_input("Faiss Path:", "../faiss_db/faiss-db-text-embedding-3-large")
        solr_url = st.text_input("Solr URL:", "http://localhost:8983/solr/vik-gpt-core/update/json/docs?commit=true")
        should_scrape = st.checkbox("Scrape Data?", value=False)
        should_faiss = st.checkbox("Update Faiss?", value=False)
        should_solr = st.checkbox("Update Solr?", value=True)

        if st.button("Execute TAD Pipeline"):
            # Here you would call tad_pipeline with the collected parameters
            tad_process.tad_pipeline(model_name, url, base_url, save_path, tad_faiss_path, solr_url, should_scrape, should_faiss, should_solr)

            st.success("TAD Pipeline executed successfully!")

    elif pipeline == "TVSZ":
        st.subheader("TVSZ Configuration")
        document_path = st.text_input("Document Path:", "../documents/BME_TVSZ_2016_elfogadott_mod_20220928_T.pdf")
        embedding_model_name = st.text_input("Embedding Model Name:", "text-embedding-3-large")
        faiss_db_path = st.text_input("Faiss DB Path:", f"../faiss_db/faiss-db-{embedding_model_name}")
        solr_url = st.text_input("Solr URL:", "http://localhost:8983/solr/vik-gpt-core/update/json/docs?commit=true")
        create_embedding = st.checkbox("Create Embedding?", value=False)
        upload_to_solr = st.checkbox("Upload to Solr?", value=True)
        upload_to_solr = st.checkbox("Upload to Solr?", value=True)

        if st.button("Execute TVSZ Pipeline"):
            # Here you would call tvsz_pipeline with the collected parameters
            tvsz_process.tvsz_pipeline(document_path, embedding_model_name, faiss_db_path, solr_url, create_embedding, upload_to_solr)

            st.success("TVSZ Pipeline executed successfully!")

# run_data_app()

