import os
import json
import re
from uuid import uuid4
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
import logging
import time
from langchain.embeddings.openai import OpenAIEmbeddings


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_all_tad_urls(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        course_links = [link['href'] for link in links if 'kepzes/targyak/' in link['href']]
        logging.info(f"Found {len(course_links)} course links.")
        return course_links
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve webpage: {e}")
        return []

def hungarian_date_to_english(date_str):
    hungarian_months = {
        "január": "January", "február": "February", "március": "March",
        "április": "April", "május": "May", "június": "June",
        "július": "July", "augusztus": "August", "szeptember": "September",
        "október": "October", "november": "November", "december": "December"
    }
    for hu, en in hungarian_months.items():
        date_str = date_str.replace(hu, en)
    return date_str

def scrape_course(url):
    try:
        logging.info(f'Scraping:  {url}')
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for course expiry
        if "Tantárgy lejárati dátuma:" in soup.text:
            logging.info('Course expired')
            return None

        # Parsing course details
        date_tag = soup.find('p', class_='date')
        date_text = None if date_tag is None else re.search(r'\d{4}.\s?\w+.\s?\d{1,2}.', date_tag.text)
        formatted_date = None
        if date_text:
            date_text = date_text.group()
            date_text_english = hungarian_date_to_english(date_text)
            formatted_date = datetime.strptime(date_text_english, '%Y. %B %d.').strftime('%Y-%m-%d')

        table = soup.find('table', align='center', border='1', cellpadding='4', cellspacing='2', width='600')
        if not table:
            return None

        rows = table.find_all('tr')[1:]
        course_data = []
        for row in rows:
            cols = [ele.text.strip() for ele in row.find_all('td')]
            title = soup.find('p', class_='title').text.strip()
            return {
                'id': cols[0],
                'credit': cols[3],
                'type': cols[2],
                'semester': cols[1],
                'title': title,
                'last_modified': formatted_date,
                'data_type': 'tad_page',
                'source': url,
            }
        # return course_data
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve webpage: {e}")
        return None

def get_all_text_from_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve webpage: {e}")
        return None

def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')

def keep_most_recent_courses(course_data):
    courses_by_title = {}
    # print(course_data)
    for course in course_data:
        # print(course)
        title = course['metadata']['title']
        date = parse_date(course['metadata']['last_modified'])
        if title not in courses_by_title or date > parse_date(courses_by_title[title]['metadata']['last_modified']):
            courses_by_title[title] = course
    return list(courses_by_title.values())

def scrape_all_tad(url, base_url, save_path):
    # url = "https://portal.vik.bme.hu/kepzes/targyak/?order=s.code&own=&department_id=all&has_datasheet=all&active=1&program=all"
    # base_url = 'https://portal.vik.bme.hu'

    course_links = get_all_tad_urls(url)
    courses_data = []
    for i in tqdm(range(len(course_links)), desc="Scraping courses"):
        course_data_metadata = scrape_course(base_url + course_links[i])
        course_data_text = get_all_text_from_website(base_url + course_links[i])
        scraped_data = {
            "metadata": course_data_metadata,
            "page_content" : course_data_text
        }
        # print(scraped_data)
        if course_data_metadata != None:
            courses_data.append(scraped_data)
    # courses_data = [data for data in courses_data if data != None]
    updated_course_data = keep_most_recent_courses(courses_data)
    file_path = save_path

    with open(file_path, 'w') as file:
        json.dump(updated_course_data, file)

    return updated_course_data


def upload_to_faiss(course_data, embeddings, faiss_path):

    documents = []

    for i, record in enumerate(tqdm(course_data)):
        # first get metadata fields for this record
        metadata = record['metadata']
        documents.append(Document(
                page_content=record['page_content'],
                metadata={
                    "data_type_s": metadata["data_type"],
                    "source_s": metadata['source'],
                }
            ))
        
    if os.path.exists(faiss_path):
        logging.info(f'Loading FAISS db')

        db = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
    else:
        logging.info(f'Creating FAISS db')

        db = FAISS.from_texts([''], embeddings)
    
    def chunked_iterable(iterable, size):
        for i in range(0, len(iterable), size):
            yield iterable[i:i + size]

    # Adding documents in batches of 10
    for chunk in chunked_iterable(documents, 10):
        db.add_documents(documents=chunk)
        time.sleep(1)
    db.save_local(faiss_path)

def upload_to_solr(solr_url, documents):

    headers = {'Content-type': 'application/json'}
    for doc in tqdm(documents, desc="Adding documents"):
        # Prepare the Solr document based on the specified structure
        solr_doc = {
            "id": str(uuid4()),  # Generating a new UUID for each document
            # "credit_i": int(doc["metadata"]["credit"]),  # Assuming credit is numeric
            # "type_s": doc["metadata"]["type"],
            # "semester_s": doc["metadata"]["semester"],
            # "title_t": doc["metadata"]["title"],  # Solr field for searchable course title
            # "last_modified_dt": doc["metadata"]["last_modified"],
            "data_type_s": doc["metadata"]["data_type"],
            "source_s": doc['metadata']['source'],
            "page_content_t": doc["page_content"]  # Solr field for storing searchable content
        }
        
        # Send the document to Solr
        response = requests.post(solr_url, headers=headers, data=json.dumps(solr_doc))
        if response.status_code == 200:
            logging.info(f'Successfully indexed document {doc["metadata"]["id"]}')
        else:
            logging.error(f'Error indexing document {doc["metadata"]["id"]}: {response.text}')


def tad_pipeline(model_name, url, base_url, save_path, tad_faiss_path, solr_url,should_scrape, should_faiss, should_solr):
    if should_scrape:
        courses = scrape_all_tad(url, base_url, save_path)
   

    with open(save_path, 'r') as file:
        courses = json.load(file)
    if should_faiss:
        embeddings = OpenAIEmbeddings(
            model=model_name,
        )
        upload_to_faiss(courses, embeddings, tad_faiss_path)
    if should_solr:
        upload_to_solr(solr_url, courses)
