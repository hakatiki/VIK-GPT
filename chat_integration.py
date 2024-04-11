import streamlit as st
import time
import json
import os
from datetime import datetime

import sys
import os

# Append the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Now you can import your module
from qa_v2 import router


def save_conversation():
    conversation_json = json.dumps(st.session_state.messages)
    timestamp = st.session_state.history_id
    filename = f"conversation_{timestamp}.json"
    os.makedirs('conversations', exist_ok=True)
    with open(os.path.join('conversations', filename), 'w', encoding='utf-8') as file:
        file.write(conversation_json)

def run_chat_app():

    st.title("VIK GPT")

    

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

