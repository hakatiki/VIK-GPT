import streamlit as st
from qa import router
import time
import json
import os
from datetime import datetime
from langchain_setup import reset_models


def save_conversation():
    conversation_json = json.dumps(st.session_state.messages)
    timestamp = st.session_state.history_id
    filename = f"conversation_{timestamp}.json"
    os.makedirs('conversations', exist_ok=True)
    with open(os.path.join('conversations', filename), 'w', encoding='utf-8') as file:
        file.write(conversation_json)

st.title("VIK GPT")

st.sidebar.title("Konfiguráció")
uploaded_api_key = st.sidebar.text_input("Itt add hozzá az API kulcsod:", type="password")

if uploaded_api_key:
    print(uploaded_api_key)
    reset_models(uploaded_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history_id" not in st.session_state:
    st.session_state.history_id = datetime.now().strftime("%Y%m%d%H%M%S")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Hány éves a BME?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_conversation()
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):

        message_placeholder = st.empty()
        # Call your custom function to get a response
        assistant_response = router(history=st.session_state.messages, query=prompt,)
        print(st.session_state.messages)
        full_response = ""

        for char in assistant_response:
            full_response += char
            time.sleep(0.03)  # Delay between each character
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_conversation()

