import os
import json
import time
import logging
from uuid import uuid4
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def vikwiki_pipeline(model_name, url, base_url, save_path, tad_faiss_path, solr_url, should_scrape, should_faiss, should_solr):
    if should_scrape:
        logging.info(f'Successfully indexed document {url}')

        courses = scrape_all_vikwiki(url, base_url, save_path)

    with open(save_path, 'r', encoding='utf-8') as file:
        courses = json.load(file)
        
    if should_faiss:
        embeddings = OpenAIEmbeddings(model=model_name)
        upload_to_faiss(courses, embeddings, tad_faiss_path)
        
    if should_solr:
        upload_to_solr(solr_url, courses)

def upload_to_faiss(data, embeddings, faiss_path):
    documents = [Document(page_content=record['page_content_t'], metadata={"data_type_s": record["data_type_s"], "source_s": record['source_s']}) for record in tqdm(data)]
    
    db = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True) if os.path.exists(faiss_path) else FAISS.from_texts([''], embeddings)

    def chunked_iterable(iterable, size):
        for i in range(0, len(iterable), size):
            yield iterable[i:i + size]

    for chunk in chunked_iterable(documents, 10):
        db.add_documents(documents=chunk)
        time.sleep(1)
    db.save_local(faiss_path)

def upload_to_solr(solr_url, documents):
    headers = {'Content-type': 'application/json'}
    for doc in tqdm(documents, desc="Adding documents"):
        solr_doc = {"id": doc["id"], "data_type_s": doc["data_type_s"], "source_s": doc['source_s'], "page_content_t": doc["page_content_t"]}
        response = requests.post(solr_url, headers=headers, data=json.dumps(solr_doc))
        
        if response.status_code == 200:
            logging.info(f'Successfully indexed document {doc["id"]}')
        else:
            logging.error(f'Error indexing document {doc["id"]}: {response.text}')

def scrape_all_vikwiki(url, domain_filter, save_path):
    links = further_filter(get_links(url, domain_filter))
    logging.info(f"URLs scraped: {len(links)}")

    contents = []
    for link in tqdm(links):
        # logging.info(f"URLs scraped: {len(links)}")

        content = scrape_content(link)
        contents.append(
            {
                'id': str(uuid4()),
                'data_type_s': 'vik_wiki',
                'source_s': link,
                'page_content_t': content
            }
        )
    save_to_json(save_path, contents)

def save_to_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_links(url, domain_filter):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return [urljoin(url, link['href']) for link in soup.find_all('a', href=True) if urlparse(urljoin(url, link['href'])).netloc == domain_filter and '#' not in urlparse(urljoin(url, link['href'])).fragment]
    else:
        logging.error("Failed to retrieve the webpage")
        return []

def further_filter(links):
    return [link for link in links if "#" not in link]

def scrape_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return '\n'.join([p.get_text() for p in soup.find_all('p')])
        else:
            logging.error(f"Failed to retrieve the webpage with status code: {response.status_code}")
            return ""
    except requests.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return ""
