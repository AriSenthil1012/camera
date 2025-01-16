import os
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from graph import invoke_our_graph
from st_callable_util import get_streamlit_cb  # Utility function to get a Streamlit callback handler with context

load_dotenv()


if "messages" not in st.session_state:
    # default initial message to render in message state
    st.session_state["messages"] = [AIMessage(content="How can I help you?")]

# Loop through all messages in the session state and render them as a chat on every st.refresh mech
for msg in st.session_state.messages:
    # https://docs.streamlit.io/develop/api-reference/chat/st.chat_message
    # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
    if type(msg) == AIMessage:
        st.chat_message("assistant").write(msg.content)
    if type(msg) == HumanMessage:
        st.chat_message("user").write(msg.content)

# takes new input in chat box from user and invokes the graph
if prompt := st.chat_input():
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
            st.write(prompt)

    # Process the AI's response and handles graph events using the callback mechanism
# Process AI response
    with st.chat_message("assistant"):
        # Create placeholder for the final message
        msg_placeholder = st.empty()
        
        # Create placeholder for streaming events
        stream_placeholder = st.empty()
        
        # Show loading animation while processing
        with stream_placeholder:
            with st.spinner("AI is thinking..."):
                # Get callback handler
                st_callback = get_streamlit_cb(stream_placeholder)
                
                # Invoke graph with callback
                try:
                    response = invoke_our_graph(st.session_state.messages, [st_callback])
                    last_msg = response["messages"][-1].content
                    
                    # Add response to session state
                    st.session_state.messages.append(AIMessage(content=last_msg))
                    
                    # Update final message placeholder
                    msg_placeholder.write(last_msg)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                finally:
                    # Clear streaming placeholder
                    stream_placeholder.empty()