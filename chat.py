import streamlit as st
from qa import router
import time

st.title("VIK GPT")

# Initialize session state variables
def initialize_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# initialize_state("presentation_index", 0)
# initialize_state("openai_model", "gpt-4-32k")
initialize_state("messages", [])

# Function to display chat messages
def display_chat_messages(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

display_chat_messages(st.session_state.messages)

# Chat input handling
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    assistant_response = router(history=st.session_state.messages, query=prompt)

    # Function to simulate streaming of response
    def simulate_response(response):
        full_response = ""
        message_placeholder = st.empty()
        for char in response:
            full_response += char
            time.sleep(0.03)  # Delay between each character
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        return full_response

    full_response = simulate_response(assistant_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
