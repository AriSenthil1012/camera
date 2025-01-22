import os 
from dotenv import load_dotenv


import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from graph import invoke_our_graph
from st_callable_util import get_streamlit_cb


# Initialize the session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content="Hello!")]

# Loop through all messages and display them
for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)

# Handle new user input
if prompt := st.chat_input():
    # Add user message to session state and display it
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)
    
    # Process AI response
    with st.chat_message("assistant"):
        # Create container for streaming
        response_container = st.container()
        
        # Get AI response
        with response_container:
            st_callback = get_streamlit_cb(response_container)
            response = invoke_our_graph(st.session_state.messages, [st_callback])
            
            # Display the response immediately
            latest_response = response["messages"][-1].content
            st.write(latest_response)
            
            # Add to session state after displaying
            st.session_state.messages.append(AIMessage(content=latest_response))
    