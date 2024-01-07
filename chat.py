import streamlit as st
from qa import router
import time
import os


st.title("VIK GPT")

st.sidebar.title("Konfiguráció")
uploaded_api_key = st.sidebar.text_input("Itt add hozzá az API kulcsod:", type="password")

# You can then use this API key in your application, 
# for example, setting it as an environment variable or directly using it in functions
if uploaded_api_key:
    # Assuming you want to set it as an environment variable
    os.environ['OPENAI_API_KEY'] = uploaded_api_key

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Hány éves a BME?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
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