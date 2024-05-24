from langchain.vectorstores import Pinecone
import langchain
from langchain.document_loaders import PyPDFLoader
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

import requests
from datetime import datetime
import asyncio  # Import asyncio for handling asynchronous tasks

from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate

from langchain_setup import *
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
import logging
import os
import hashlib
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('LLM:')
print(llm_gpt3)
print(llm_gpt4)
print('EMB:')
print(embeddings)
core_name = "/vik-gpt-core-bench"


# Get the Solr URL from environment variable
solr_url_beginning = os.getenv('SOLR_URL', 'http://localhost:8983/solr')

solr_url = f"{solr_url_beginning}{core_name}/select"
SOLR_COUNT = 4
EMBEDDING_COUNT = 4

metadata_descriptions = {
    'tvsz_paragraph': 'Ez a szöveg a BME Tanulmányi és Vizsga szabályzatából származik. A szöveg paragrafusokra van ' +
                    'bontva számodra. Fontos a forrás és a pontos idézés ha ilyen típusú szöveggel dolgozol.'+
                    'Azonosítónak használhatod a pragrafust, például BME TVSZ 21. paragrafus.',
    'tad_page': 'Ez a szöveg a BME VIK tárgyoldaláról van letöltve. A tárgyak típusának értelmezése: 4/2/0/v ' +
                '(előadás/gyakorlat/labor/vizsga) Vizsgával záruló tárgyak "v"-vel, félévközi tárgyak "f"-fel jelölve. ' + 
                'Egy félévben 30 kredit teljesítése szükséges. Azonosítónak használd a tárgy címét és kódját.',
    'vikwiki': 'Ez a szöveg a VIK wikipedia oldaláról származik, a hallgatók állították össze.' +
                'Tartalma gyakran pontatlan, elavult vagy hibás lehet. ' + 
                'Ha ilyen dokumentumot idézel mindenképp érdemes ezt kihangsúlyoznod.',
}
def reset_models(key):
    precomputed_hash = 'e27acbc27ea0fdc64e8648bd51d8f19bf271e1372889b506c28809211dfbd335'
    hash_object = hashlib.sha256(key.encode())
    hex_dig = hash_object.hexdigest()
    logging.info(f"{hex_dig}")
    logging.info(f"{key}")

    print(hex_dig)
    print(key)
    if hex_dig == precomputed_hash:
        print(key)
        with open('.apikey', 'r') as file:
            key = file.read().strip()
    os.environ['OPENAI_API_KEY'] = key
    global llm_gpt3, llm_gpt4, embedding_model, vectorstore
    llm_gpt3 = chat_models.ChatOpenAI(model_name=gpt3_model_name, temperature=0.0, openai_api_key=key)
    llm_gpt4 = chat_models.ChatOpenAI(model_name=gpt4_model_name, temperature=0.0, openai_api_key=key)
    embedding_model = embeddings.openai.OpenAIEmbeddings(model=embedding_model_name, openai_api_key=key)
    vectorstore = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
    
    print("Models and dependencies have been reset with the new API key.")
    
def extract_keywords(query,context):

    extractor = PromptTemplate.from_template(
        template=(
            'Your task is to extract the keywords of the user query and optionally add keywords if you find them relevant. '
            'Make sure it is in Hungarian, use at least 3 keywords. '
            'Example: Milyen játékelméletről szóló tárgyak vannak? '
            'Output: játékelmélet, nash egyensúly, fogolydilemma. '
            'The context of the conversation is the following:'
            '{context}'
            'The most recent message by the user is:'
            '{query}'
            'Generated keywords for a Solr search:'
        )
    )
    chain = extractor|llm_gpt4
    logging.info(f"Extracting keywords for query: {query}")
    keywords = chain.invoke({'query':query, 'context':context})
    logging.info(f"Extracted keywords: {keywords}")

    return keywords.content

def unify_metadata_embeddings(data):
    print(data)
    return {
        'page_content_t': data.page_content,
        'source_s': data.metadata['source_s'],
        'data_type_s': data.metadata['data_type_s']
    }

def solr_retrieve(keywords):
    params = {
        "q": keywords,
        "defType": "edismax",
        "qf": "page_content_t",
        "wt": "json",
        "rows": SOLR_COUNT,
    }
    response = requests.get(solr_url, params=params)
    if response.status_code == 200 and response.json()['response']['numFound'] > 0:
        return response.json()['response']['docs']
    else:
        return solr_url

def get_solr_url():
    return solr_url

def embedding_retrieve(query):
    docs =  vectorstore.max_marginal_relevance_search(query=query, k=EMBEDDING_COUNT, fetch_k=50)
    return [unify_metadata_embeddings(doc) for doc in docs]


def make_unique(embedding_retrieved, solr_retrieved):
    combined_documents = embedding_retrieved + solr_retrieved
    returned_documents = []
    
    for i, doc in enumerate(combined_documents):
        current_text = doc['page_content_t']
        is_unique = True
        for other_doc in combined_documents[i+1:]:
            other_text = other_doc['page_content_t']
            if current_text == other_text:
                is_unique = False
                break
        if is_unique:
            returned_documents.append(doc)
    return returned_documents


def unified_retrieval(query, context):
    keywords = extract_keywords(query, context)
    documents_solr = solr_retrieve(keywords)
    documents_embs = embedding_retrieve(query)
    unique_documents = make_unique(documents_solr, documents_embs)
    logging.info(f"Retrieved documents: {len(unique_documents)}")

    compressed_docs = asyncio.run(compress_documents(unique_documents, context))
    print("COMPRESSED STUFF")
    print(compressed_docs)

    return compressed_docs

async def compress_documents(documents, context):

    qa = PromptTemplate.from_template(
        template=(
            'A BME diákjainak segítő chatbot vagyok. '
            'Felhasználva a megadott dokumentumokat válaszolok a kérdésre. '
            'A jelenlegi feladatom az, hogy a megadott dokumentumról eldöntsem, hogy releváns vagy sem. '
            'Ha nem releváns, annyit válaszolok, hogy nem releváns. '
            'Ha releváns, akkor összegyűjtöm az információkat a dokumentumból és összefoglalom úgy, hogy a kérdésre a lehető legjobb választ adja. '
            'Röviden összefoglalva, a dokumentumban található információ tömörítése a feladatom a kérdés függvényében. '
            'A tömörítés elejére egy külön sorba, röviden helyezzel el valami egyedi azonosítót a szöveg alapján. Ha van metadat, ami a szöveg értelmezését segíti, az adhat útmutatást. '
            'A dokumentum forrása: {source}. '
            'A dokumentum metaadta az értelmezéshez: {metadata}. '
            'A dokumentum: {document}. '
            'A felhasználó kérdése: {context}.'
        )
    )
    chain = qa | llm_gpt4

    # Create a coroutine list for all document processing
    coroutines = [
        chain.ainvoke({
            'context': context,
            'document': doc['page_content_t'],
            'metadata': metadata_descriptions.get(doc['data_type_s'], 'Nem elérhető leírás'),
            'source': doc['source_s']
        }) for doc in documents
    ]

    # Gather all coroutines to run them concurrently
    compressed_docs = await asyncio.gather(*coroutines)
    print("RETURNED STUFF")
    print(compressed_docs)
    return [doc.content for doc in compressed_docs]

# def compress_documents(documents, context):

#     qa = PromptTemplate.from_template(
#         template=(
#             'A BME diákjainak segítő chatbot vagyok. '
#             'Felhasználva a megadott dokumentumokat válaszolok a kérdésre '
#             'A jelenlegi feladatom az, hogy a megadott dokumentumról eldöntsem, hogy releváns vagy sem'
#             'Ha nem releváns annyit válaszolok, hogy nem releváns'
#             'Ha releváns akkor összegyűjtöm az információkat a dokumentumból és összefoglalom úgy, hogy a kérdésre a lehető legjobb választ adja.'
#             'Röviden összefoglalva a dokumentumban található információ tömörítése a feladatom a kérdés függvényében.'
#             'A tömörítés elejére egy külön sorba, röviden helyezzel el valami egyedi azonosítót a szöveg alapján. Ha van metadat ami a szöveg értelmezését segíti az adhat útmutatást.'
#             'A dokumentum forrása: {source}'
#             'A dokumentum metaadta az értelmezéshez: {metadata}'
#             'A dokumentum: {document}'
#             'A felhasználó kérdése: {context}'
#         )
#     )
#     chain = qa | llm_gpt4
#     compressed_docs = []
#     for doc in documents:
#         document_text =  doc['page_content_t']
#         metadata_text = metadata_descriptions.get(doc['data_type_s'],'Nem elérhető leírás')
#         source_text = doc['source_s']
        
#         compressed_doc = chain.invoke(
#             {
#                 'context': context, 
#                 'document':document_text,
#                 'metadata':metadata_text,
#                 'source':source_text
#             },).content
#         compressed_docs.append(compressed_doc)
#     # logging.info(f"Compressed documents: {compressed_docs}")

#     return compressed_docs



def generate_answers(query, context):
    compressed_docs = unified_retrieval(query,context)
    compressed_docs_str = '\n\n'.join(compressed_docs)
    current_time = datetime.now().strftime("%Y-%m-%d")
    
    template = ChatPromptTemplate.from_template(
        f'''
        Jelenlegi idő: {current_time}. Te egy chatbot vagy, amelynek célja, hogy segítséget nyújtson a BME hallgatóinak. Fő feladatod, hogy hasznos válaszokat adj a rendelkezésre álló kontextus és a lekérdezett, tömörített dokumentumok alapján. Ha közvetlenül nem tudsz válaszolni, használd a "RAG_RETRIEVE" jelzést, ami azt jelzi, hogy szükség van külső keresésre, ezt követően befejezed a generálást. 
        Preferenciád, hogy magyar nyelven válaszolj.
        A beszélgetésünk eddigi kontextusa a következő:
        {context}
        A legutolsó üzenet a beszélgetésben ami a legrelevánsabb:
        {query}
        Az utolsó üzenet a kontextusban az aktuális kérdés, amire válaszolnod kell. Ne feledd, elsődleges célod a hallgatók hatékony segítése a rendelkezésre álló információk felhasználásával, vagy jelezni, amikor további keresés szükséges.
        A lekérdezett, tömörített dokumentumok amik relevánsak lehetnek:
        {compressed_docs_str}
        A válaszaidhoz használd fel a forrásokat (SOURCE) is ha tudod.
        '''
    )
    chain = template | llm_gpt4
    response = chain.invoke({'current_time': current_time, 'context': context, 'compressed_docs': compressed_docs_str}).content
    # logging.info(f"Generated response: {response}")

    return response


def generate_context_from_history(history):
    context = ''
    messages = [f"{message['role']}:{message['content']}\n" for message in history]
    messages = '\n'.join(messages)
    max_length = min(5000,len(messages))
    begin = len(messages)-max_length
    context = messages[begin:]
    return context


def router(query, history=[]):
    context = generate_context_from_history(history)
    # logging.info(f"Generated context from conversation history: {context}")

    current_time = datetime.now().strftime("%Y-%m-%d")

    routing_template = ChatPromptTemplate.from_template(
        f'''
        It's currently {current_time}, and you're a chatbot designed to assist BME students with their inquiries. Your main task is to provide helpful responses based on the provided context. If you're unable to answer directly, you should use "RAG_RETRIEVE" to indicate a need for external search, ending the generation thereafter. 
        In case you use "RAG_RETRIEVE" you can query information on courses and various other things.
        You prefer to answer in Hungarian.
        The context of our conversation so far is:
        {context}
        The latest message is:
        {query}
        The last message in the context is the current query you need to respond to. Remember, your priority is to assist the students effectively, using the resources available or indicating when a search is needed.
        '''
    )

    routing_chain = routing_template | llm_gpt4
    response = routing_chain.invoke({'current_time': current_time, 'context': context}).content
    logging.info(f"Generated response: {response}")

    if 'RAG_RETRIEVE' in response:
        return generate_answers(query, context)
    return response

