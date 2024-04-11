import streamlit as st
from chat import run_chat_app

# Page selection
page = st.sidebar.selectbox("Choose your page", ["Chat", "Data"])

if page == "Chat":
    run_chat_app()  # Call a function that renders Page 1

