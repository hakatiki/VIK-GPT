
import os
import json
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from tqdm.auto import tqdm
from uuid import uuid4
import requests
import logging
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def tvsz_pipeline(pdf_path, embeddings, faiss_path, solr_url,create_embedding =True, upload_to_solr = True):
    # Load environment variables
    load_dotenv()
    logging.info(f'Processing:  {pdf_path}')


    # Access the OpenAI API key from environment variables
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found in environment variables")

    # If needed, set it as an environment variable for other modules
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

    # Function to remove dashes from text
    def remove_dashes(text):
        return text.replace("-\n", "")

    # Load and split PDF document
    loader = PyPDFLoader(pdf_path)
    documents = loader.load_and_split()

    def remove_dashes(text):
        return text.replace("-\n", "")
    paragraph_splitters_1 = [f" {paragraph}. §" for paragraph in range(1, 242)]
    paragraph_splitters_2 = [f"\n{paragraph}. §" for paragraph in range(1, 242)]

    document = ""
    for doc in documents:
        document += "\n" + doc.page_content
    document = remove_dashes(document)
    logging.info(f'Length of the document is: {len(document)}')
    
    split_locations = [0]
    for (paragraph1, paragraph2) in zip(paragraph_splitters_1, paragraph_splitters_2):
        loc1 = document[split_locations[-1]:].find(paragraph1)
        loc2 = document[split_locations[-1]:].find(paragraph2)
        if loc1 == -1:
            loc1 = 10**10
        if loc2 == -1:
            loc2 = 10**10
        if loc1 == 10**10 and loc2 == 10**10:
            print(paragraph1)
            print("error")
        else:
            split_locations.append(min(loc1, loc2)+split_locations[-1])
    split_documents = []
    for i in range(len(split_locations)-1):
        split_documents.append(document[split_locations[i]:split_locations[i+1]])
    logging.info(f'Number of paragraphs processed:  {len(split_documents)}')

    # Function to get page number of a paragraph
    def get_page_number(paragraph):
        for (page, doc) in zip(range(len(documents)), documents):
            if paragraph[:100].strip() in doc.page_content:
                return page-1
        return -1
    # Prepare embeddings
    # print(split_documents)

    logging.info(f'Creating FAISS ')
    # Prepare documents and metadata
    documents_list = []
    for i, record in enumerate(tqdm(split_documents[1:])):
        metadata = {
            'data_type_s': 'tvsz_paragraph',
            # 'paragraph': f"{{i+1}}. §",
            # 'page': f"{{get_page_number(record)}}. oldal",
            'source_s': f"PDF elérési út: 'https://www.kth.bme.hu/document/2748/original/BME_TVSZ_2016_elfogadott_mod_20220928_T.pdf'\nParagrafus: {i+1}. §\nOldalszám: {get_page_number(record)}",
            # 'title': "BME TVSZ 2016",
            # 'text': record.strip(),
            # 'page_content': record.strip()
        }
        documents_list.append(Document(page_content=record.strip(), metadata=metadata))
        # print(len(record.strip()))
    # print(len(documents_list))
    if create_embedding:
        if os.path.exists(faiss_path):
            logging.info(f'Loading FAISS db')

            db = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
        else:
            logging.info(f'Creating FAISS db')

            db = FAISS.from_texts([''], embeddings)
        
        def chunked_iterable(iterable, size):
            for i in range(0, len(iterable), size):
                yield iterable[i:i + size]
        # # Adding documents in batches of 10
        for chunk in chunked_iterable(documents_list, 10):
            db.add_documents(documents=chunk)

            time.sleep(1)
        db.save_local(faiss_path)
        logging.info(f'Saved FAISS db')

    if upload_to_solr:
        logging.info(f'Adding data to Solr')

        headers = {'Content-type': 'application/json'}
        for doc in tqdm(documents_list, desc="Adding documents"):
            # Assuming 'documents' is a list of 'Document' objects with 'metadata' and 'page_content'
            solr_doc = {
                "id": str(uuid4()),  # Generating a new UUID for each document
                # "credit_i": int(doc.metadata.get("credit", 0)),  # Example for converting credit to int
                # "type_s": doc.metadata.get("type", ""),
                # "semester_s": doc.metadata.get("semester", ""),
                # "title_t": doc.metadata.get("title", ""),
                # "last_modified_dt": doc.metadata.get("last_modified", ""),
                "data_type_s": doc.metadata["data_type_s"],
                "source_s": doc.metadata["source_s"],
                "page_content_t": doc.page_content
            }
            
            # Send the document to Solr
            response = requests.post(solr_url, headers=headers, json=solr_doc)
            if response.status_code == 200:
                logging.info(f'Successfully indexed document {solr_doc["id"]}')
            else:
                logging.error(f'Error indexing document {solr_doc["id"]}: {response.text}')

    return documents_list


# embedding_model_name = "text-embedding-ada-002"
# data = tvsz_pipeline(
#     "C:/Users/takat/OneDrive/Documents/Egyetem/Diploma/documents/BME_TVSZ_2016_elfogadott_mod_20220928_T.pdf",
#     embedding_model_name,
#     f"../faiss_db/faiss-db-ada-002",
#     "http://localhost:8983/solr/vik-gpt-core/update/json/docs?commit=true",
#     create_embedding=False,
#     upload_to_solr=False
# )