import streamlit as st
from chat_integration import run_chat_app
from data_integration import run_data_app
from query_integration import run_query_app
from qa_v2 import reset_models
import os
from dotenv import load_dotenv

# Load initial API key from .env file
load_dotenv(override=True)

def get_api_key():
    # Attempt to get the API key from Streamlit's session state
    return st.session_state.get('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))

def update_api_key(key):
    # Update the API key in Streamlit's session state and reset the models
    st.session_state['OPENAI_API_KEY'] = key
    print("wtf")
    reset_models(key)  # Assuming reset_models re-initializes any needed models with the new key

# Ensure the API key is loaded into session state upon app start/reload
if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# Sidebar for API key input and page selection
st.sidebar.title("Configuration")
uploaded_api_key = st.sidebar.text_input("Add your API key here:", type="password")

if uploaded_api_key:
    update_api_key(uploaded_api_key)
    st.sidebar.success("API Key updated!")

page = st.sidebar.selectbox("Choose your page", ["Chat", "Data", "Query"], index=0)

# Main content area
if page == "Chat":
    run_chat_app()  # Function that renders the chat page
elif page == "Data":
    run_data_app()  # Function that renders the data page
elif page == "Query":
    run_query_app()  # Function that renders the query page
