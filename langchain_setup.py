import os
from langchain import vectorstores, document_loaders, embeddings, chat_models, chains, prompts
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Access the environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Model names
model_name = 'text-embedding-ada-002'
gpt3_model_name = 'gpt-3.5-turbo-1106'
gpt4_model_name = 'gpt-4'

# Loading embeddings
embeddings = embeddings.openai.OpenAIEmbeddings(model=model_name)
print('LLM is loading...')

# Loading language models
llm_gpt3 = chat_models.ChatOpenAI(model_name=gpt3_model_name, temperature=0.0)
llm_gpt4 = chat_models.ChatOpenAI(model_name=gpt4_model_name, temperature=0.0)

# Loading vectorstores
print('Vectorstores are loading...')
vectorstore_qa = vectorstores.FAISS.load_local('./faiss_db/tvsz-qa-db', embeddings)
vectorstore_tvsz = vectorstores.FAISS.load_local('./faiss_db/tvsz-db', embeddings)
vectorstore_tad = vectorstores.FAISS.load_local('./faiss_db/tad-db', embeddings)
vectorstore_tad_title = vectorstores.FAISS.load_local('./faiss_db/tad-db-title-key', embeddings)
