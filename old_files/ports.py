import streamlit as st
import subprocess
import time
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any

def simulate_stream_response(text: str):
    """
    Generator function to simulate streaming response.
    Yields one word at a time with a small delay.
    """
    words = text.split()
    for i, word in enumerate(words):
        # Add space before word, except for first word
        prefix = ' ' if i > 0 else ''
        yield prefix + word
        time.sleep(0.05)  # Small delay between words

def check_usb_devices(query_str: Any) -> Any:
    """
    A function that checks USB devices based on a user query.
    Modified to accept and return Any type for Streamlit compatibility.
    
    Args:
        query_str (Any): The user's question about USB devices from Streamlit
        
    Returns:
        Any: The final AI response message content
    """
    def list_usb_devices() -> list:
        """
        Retrieves a list of all USB devices connected to the system using the lsusb command.
        
        Returns:
            list: A list of strings representing USB devices with their details
        """
        devices = []
        result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
        for line in result.stdout.strip().split('\n'):
            devices.append(line)
        return devices

    # Set up tools
    tools = [list_usb_devices]
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4")
    llm_with_tools = llm.bind_tools(tools)
    
    # System Message
    sys_msg = SystemMessage(
        content=(
            "You are a helpful assistant tasked with identifying and managing devices connected to a system. "
            "Users may ask questions about specific devices, such as identifying a particular device, "
            "or general queries about the list of connected devices. Provide precise and detailed responses based on the input list. "
        )
    )
    
    # Node
    def assistant(state: MessagesState):
        """Process messages in the state and return LLM response."""
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
    
    # Graph setup
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    
    # Define edges
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    builder.add_edge("tools", "assistant")
    
    # Compile graph
    agent_graph = builder.compile()
    
    # Create message and get response
    messages = [HumanMessage(content=str(query_str))]
    result = agent_graph.invoke({"messages": messages})
    
    # Extract the final AI message content
    final_message = [msg for msg in result["messages"] if isinstance(msg, AIMessage)][-1]
    return final_message.content

# Set page config
st.set_page_config(page_title="Pegasus", page_icon="🦄")

# App title
st.title("Pegasus")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Hello"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from USB device checker
    response = check_usb_devices(prompt)
    
    # Display assistant response in chat message container with streaming effect
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response word by word
        for word in simulate_stream_response(response):
            full_response += word
            response_placeholder.markdown(full_response + "▌")
        
        # Show final response without cursor
        response_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})