import streamlit as st
import pyrealsense2 as rs
import numpy as np
import cv2
import subprocess
import time
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any

def simulate_stream_response(text: str):
    words = text.split()
    for i, word in enumerate(words):
        prefix = ' ' if i > 0 else ''
        yield prefix + word
        time.sleep(0.05)

def check_usb_devices(query_str: Any) -> Any:
    def list_usb_devices() -> list:
        devices = []
        result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
        for line in result.stdout.strip().split('\n'):
            devices.append(line)
        return devices

    tools = [list_usb_devices]
    llm = ChatOpenAI(model="gpt-4")
    llm_with_tools = llm.bind_tools(tools)
    
    sys_msg = SystemMessage(
        content=(
            "You are a helpful assistant tasked with identifying and managing devices connected to a system. "
            "Users may ask questions about specific devices, such as identifying a particular device, "
            "or general queries about the list of connected devices. Provide precise and detailed responses based on the input list. "
        )
    )
    
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
    
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    
    agent_graph = builder.compile()
    messages = [HumanMessage(content=str(query_str))]
    result = agent_graph.invoke({"messages": messages})
    final_message = [msg for msg in result["messages"] if isinstance(msg, AIMessage)][-1]
    return final_message.content

def main():
    # Set page config
    st.set_page_config(page_title="Pegasus", page_icon="🦄", layout="wide")
    
    # Create two columns: left (for camera feeds) and right (for chat)
    left_col, right_col = st.columns([1, 1])
    
    # Initialize RealSense pipeline
    pipe = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    
    with left_col:
        st.title("Camera Feeds")
        # Create placeholders for camera feeds
        color_frame_placeholder = st.empty()
        depth_frame_placeholder = st.empty()
    
    with right_col:
        st.title("Chat Interface")
        # Initialize chat history if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Start the RealSense pipeline
    profile = pipe.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    
    try:
        while True:
            # Process RealSense frames
            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                continue
            
            # Process color image
            color_image = np.asanyarray(color_frame.get_data())
            color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            
            # Process depth image
            depth_image = np.asanyarray(depth_frame.get_data())
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )
            depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)
            
            # Display frames in left column
            with left_col:
                color_frame_placeholder.image(
                    color_image,
                    channels="RGB",
                    use_container_width=True,
                    caption="Color Feed"
                )
                depth_frame_placeholder.image(
                    depth_colormap,
                    channels="RGB",
                    use_container_width=True,
                    caption="Depth Feed"
                )
            
            # Handle chat input in right column
            with right_col:
                # Add unique key to chat_input to avoid duplicate ID error
                if prompt := st.chat_input("Hello", key="chat_input_unique"):
                    # Add user message to chat history
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # Get and display assistant response
                    response = check_usb_devices(prompt)
                    with st.chat_message("assistant"):
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        for word in simulate_stream_response(response):
                            full_response += word
                            response_placeholder.markdown(full_response + "▌")
                        
                        response_placeholder.markdown(full_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    finally:
        pipe.stop()

if __name__ == "__main__":
    main()