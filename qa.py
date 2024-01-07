from langchain.vectorstores import Pinecone
import langchain
from langchain.document_loaders import PyPDFLoader
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
import os
import pinecone
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

print('LLM:')
print(llm_gpt3)
print(llm_gpt4)
print('EMB:')
print(embeddings)

def answer_question_tvsz(question, logging=False):

    documents = vectorstore_qa.max_marginal_relevance_search(
        query=question, 
        k=8, 
        fetch_k=50, 
        filter={"data_type": "tvsz-qa"}
    )
    if logging:
        for doc in documents:
            print(doc.page_content)

    # Join the page contents of the documents
    joined_content = '\n\n'.join(doc.page_content for doc in documents)

    # Load the QA chain with the required chain type
    qa_chain = load_qa_with_sources_chain(llm_gpt4, chain_type="stuff") 

    # Set the document prompt with structured formatting
    qa_chain.document_prompt = PromptTemplate(
        input_variables=['page_content', 'page', 'paragraph'],
        template='TARTALOM: {page_content}\nFORRÁS: TVSZ {page} - {paragraph}',
    )

    # Set the LLM chain prompt with detailed instructions and formatting
    qa_chain.llm_chain.prompt = PromptTemplate(
        input_variables=['summaries', 'question'],
        template=(
            'Adott egy hosszú dokumentum alábbi kivonatolt részei és egy kérdés, '
            'hozzon létre egy végső választ hivatkozásokkal.\n'
            'MINDIG adjon vissza egy „FORRÁS” részt a válaszában.\n\n'
            '=========\n'
            'KÉRDÉS: Hány félév átlaga számít az átsoroláshoz?\n'
            'TARTALOM: Az Egyetem a hallgatót átsorolhatja tanév végén a következő alapokon: az utolsó két aktív félév tanulmányi teljesítménye (tanulmányi eredmény alapú átsorolás), a támogatott félévek felhasználása (támogatási idő alapú átsorolás), vagy a hallgató kezdeményezése alapján. Magyar állami ösztöndíjas hallgatókat önköltséges képzésre kell átsorolni, ha az utolsó két aktív félévben nem teljesítették a megadott kreditmennyiséget vagy a súlyozott tanulmányi átlagot.\n'
            'FORRÁS: TVSZ 49. oldal - 74. §\n'
            'VÁLASZ:  Az utolsó két félév átlagát veszik figyelembe. Forrás: TVSZ 49. oldal - 74. §\n'
            'A példa vége.\n\n'
            'További dokumentumok:\n'
            '{summaries}\n'
            '=========\n'
            'Továbbá itt található pár kérdés és válasz ami releváns LEHET a kérdés megválaszolásához:\n'
            + joined_content + '\n'
            'KÉRDÉS: {question}\n'
            'VÉGSŐ VÁLASZ:'
        )
    )

    # Initialize the RetrievalQAWithSourcesChain
    chain = RetrievalQAWithSourcesChain(
        combine_documents_chain=qa_chain,
        retriever=vectorstore_tvsz.as_retriever( 
            search_type="mmr", 
            search_kwargs={
                'k': 3, 
                'fetch_k': 30,
                "filter": {"data_type": "tvsz-paragraph"}
            },
            reduce_k_below_max_tokens=True, 
            max_tokens_limit=3375, 
            verbose=True, 
            return_source_documents=True,
        )
    )

    # Execute the chain and return the result
    result = chain(question)
    return result


def compressed_tad_qa(query, logging=False):
    # Initialize the compressor with LLM GPT-3
    compressor = LLMChainExtractor.from_llm(llm_gpt3)

    # Set up the Contextual Compression Retriever
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, 
        base_retriever=vectorstore_tad.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 10, 'fetch_k': 30}
        )
    )

    # Define the prompt template for the compressor
    compression_retriever.base_compressor.llm_chain.prompt = PromptTemplate(
        input_variables=['context', 'question'],
        template=(
            'A BME diákjainak segítő chatbot vagyok. '
            'Felhasználva a tantárgyi adatlapokat, válaszolok a kérdésedre. '
            'A tárgyak információi a BEGINING_OF_COURSE_DATA és END_OF_COURSE_DATA között találhatóak. '
            'Tárgyak típusának értelmezése: 4/2/0/v (előadás/gyakorlat/labor/vizsga). '
            'Vizsgával záruló tárgyak "v"-vel, félévközi tárgyak "f"-fel jelölve. '
            'Egy félévben 30 kredit teljesítése szükséges. '
            '\n\nA megadott szöveg: BEGINING_OF_COURSE_DATA {context} END_OF_COURSE_DATA\n '
            'Ha a megadott adatlap NEM releváns akkor a válaszom rövid, tömör. Azt mondom: "Nem tudom".'
            'Ha releváns, akkor részletes és indokolt választ nyújtok.'
            'A kérdés: {question}'
        )
    )
    # Retrieve and combine compressed documents
    compressed_docs = compression_retriever.get_relevant_documents(query)
    # Format and join the documents with their metadata
    docs = '\n\n'.join([
        'BEGINING_OF_COURSE_DATA '
        f'A kurzus címe: {doc.metadata.get("course_title", "Ismeretlen cím")}, '
        f'Kreditértéke: {doc.metadata.get("course_credit", "Ismeretlen kreditérték")},'
        f'Típusa: {doc.metadata.get("course_type", "Ismeretlen típus")}, '
        f'Forrás: {doc.metadata.get("source", "Ismeretlen forrás")}, '
        f'A tárgy leírása: {doc.page_content} '
        'END_OF_COURSE_DATA'
        for doc in compressed_docs
    ])

    # Optional logging to print each document's content and metadata
    if logging:
        for doc in compressed_docs:
            print(
               'BEGINING_OF_COURSE_DATA '
                f'A kurzus címe: {doc.metadata.get("course_title", "Ismeretlen cím")}, '
                f'Kreditértéke: {doc.metadata.get("course_credit", "Ismeretlen kreditérték")},'
                f'Típusa: {doc.metadata.get("course_type", "Ismeretlen típus")}, '
                f'Kurzuskód: {doc.metadata.get("course_id", "Ismeretlen id")}, '
                f'A tárgy leírása: {doc.page_content} '
                'END_OF_COURSE_DATA'
            )
    # Set up the ChatPromptTemplate for response generation
    qa = ChatPromptTemplate.from_template(
        template=(
            'A BME diákjainak segítő chatbot vagyok. '
            'Kombináld az alábbi releváns válaszokat a felhasználó kérdésére. '
            'Jelmagyarázat: 4/2/0/v (előadás/gyakorlat/labor/vizsga). '
            'Egy félévben 30 kreditet kell teljesíteni. '
            'Az adatok a BEGINING_OF_COURSE_DATA és END_OF_COURSE_DATA között találhatóak.'
            'A válaszomhoz a lehető legtöbb információt felhasználom. '
            'Lehet, hogy egy adatlap nem releváns a kérdésre, ebben az esetben nem használom fel. '
            '\nAz eddig összegyűjtött információ:\n' + docs + 
            '\nA felhasználó eredeti kérdése: ' + query + 
            '\nA végső válaszod:'
        )
    )

    # Chain the QA template with the LLM for response generation
    chain = qa | llm_gpt4
    
    # Invoke the chain to generate the final response
    return chain.invoke({}).content


def generate_context_form_history(history):
    context = ''
    for message in history:
        current = f'''{message['role']}:{message['content']}\n'''
        context += current
    return context

def router(query, history=[], logging=True):
    # Template with context learning examples for routing
    routing_template = ChatPromptTemplate.from_template(
        '''
        A feladatot nagyon pontosan kell elvégezned. Három lehetőséged van:
        1. BME-vel kapcsolatos jogi kérdés: TVSZ_QA
        2. Tantárgyak, oktatók: TAD_QA
        3. Egyéb kérdések: GENERIC_QA
        Példák a besorolásra:
        FELHASZNÁLÓ: Ki az analízis egy tárgy oktatója? GPT-MODEL: TAD_QA
        FELHASZNÁLÓ: Segítsél nekem pythonban egy listát megfordítani? GPT-MODEL: GENERIC_QA
        FELHASZNÁLÓ: Hány kredites és mik a tárgykövetelményei a Gépi tanulás tárgynak? GPT-MODEL: TAD_QA
        FELHASZNÁLÓ: Hány éves a BME? GPT-MODEL: GENERIC_QA
        FELHASZNÁLÓ: Mi a kitüntetéses diploma kritériuma? GPT-MODEL: TVSZ_QA
        FELHASZNÁLÓ: Hány államilag támogatott félévem van? GPT-MODEL: TVSZ_QA
        FELHASZNÁLÓ: Milyen feltételekkel lehet eltérni a teljes idejű képzés kereteitől? GPT-MODEL: TVSZ_QA
        FELHASZNÁLÓ: Mi a felzárkóztató tantárgyak célja az egyetemen? GPT-MODEL: TVSZ_QA
        FELHASZNÁLÓ: Ha tegnap esett ma is esni fog? GPT-MODEL: GENERIC_QA
        FELHASZNÁLÓ: Megbuktam analizis 1-ből most mit csináljak? GPT-MODEL: TVSZ_QA
        FELHASZNÁLÓ: Milyen témákat dolgoznak fel analizis 1-en? GPT-MODEL: TAD_QA
        FELHASZNÁLÓ: ''' + query + ''' GPT-MODEL:'''
    )

    # Create the routing chain
    routing_chain = routing_template | llm_gpt4

    # Invoke the routing chain and determine the mode
    router_mode = routing_chain.invoke({}).content

    if logging:
        print(f"Router Mode: {router_mode}")

    answer = ''
    if router_mode == 'TVSZ_QA':
        if logging:
            print("Routing to TVSZ QA")
        answer =  answer_question_tvsz(query, logging=logging)['answer']
    elif router_mode == 'TAD_QA':
        if logging:
            print("Routing to TAD QA")
        answer =  compressed_tad_qa(query, logging=logging)

    if logging:
        print("Routing to GENERIC QA")
    generic_qa_template = ChatPromptTemplate.from_template(
        '''
        Egy segítőkész aszisztensként a feladatom a BME hallgatóinak kérdéseire válaszolni. 
        Amennyiben már rendelkezésre áll egy részleges válasz, formázzam azt úgy, hogy stílusosan illeszkedjen a meglévő kontextushoz. 
        Ha még nincs előzőleg generált válasz, akkor most hozzak létre egyet. 
        Fontos, hogy a válaszom pontos, tájékoztató és releváns legyen a felvetett kérdésre. 

        Az eddigi kontextus: {context}
        A hallgató kérdése: {query}
        Az eddig generált válasz (ha van): {answer}

        A végső válaszom:'''

    )
    generic_qa_chain = generic_qa_template | llm_gpt4
    context = generate_context_form_history(history)
    if logging:
        print(f"Context: {context}")
    return generic_qa_chain.invoke({'query': query, 'answer': answer, 'context': context}).content
