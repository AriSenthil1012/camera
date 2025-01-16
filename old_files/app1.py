import os
from dotenv import load_dotenv
import streamlit as st
import pyrealsense2 as rs
import numpy as np
import cv2
from langchain_core.messages import AIMessage, HumanMessage
from graph import invoke_our_graph
from st_callable_util import get_streamlit_cb

def setup_realsense():
    pipe = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    profile = pipe.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    return pipe

def process_camera_feeds(pipe):
    frames = pipe.wait_for_frames()
    color_frame = frames.get_color_frame()
    depth_frame = frames.get_depth_frame()
    
    if not color_frame or not depth_frame:
        return None, None
    
    color_image = np.asanyarray(color_frame.get_data())
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
    depth_colormap = cv2.applyColorMap(
        cv2.convertScaleAbs(depth_image, alpha=0.03),
        cv2.COLORMAP_JET
    )
    depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)
    return color_image, depth_colormap

def main():
    st.set_page_config(layout="wide")
    load_dotenv()

    # Create the basic two-column layout
    left_col, right_col = st.columns([0.6, 0.4])
    
    # Left column content
    color_placeholder = left_col.empty()
    depth_placeholder = left_col.empty()
    
    # Right column content
    right_col.header("Chat")
    if "messages" not in st.session_state:
        st.session_state["messages"] = [AIMessage(content="How can I help you?")]

    # Display chat messages
    for msg in st.session_state.messages:
        if isinstance(msg, AIMessage):
            right_col.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            right_col.chat_message("user").write(msg.content)

    # Chat input
    if prompt := right_col.chat_input("Hello..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        right_col.chat_message("user").write(prompt)

        msg_placeholder = right_col.empty()
        stream_placeholder = right_col.empty()
        
        with stream_placeholder:
            with st.spinner("AI is thinking..."):
                st_callback = get_streamlit_cb(stream_placeholder)
                try:
                    response = invoke_our_graph(st.session_state.messages, [st_callback])
                    last_msg = response["messages"][-1].content
                    msg_placeholder.write(last_msg)
                    st.session_state.messages.append(AIMessage(content=last_msg))
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                finally:
                    stream_placeholder.empty()

    # Camera feed processing
    try:
        pipe = setup_realsense()
        while True:
            color_image, depth_colormap = process_camera_feeds(pipe)
            
            if color_image is not None and depth_colormap is not None:
                color_placeholder.image(
                    color_image,
                    channels="RGB",
                    use_container_width=True,
                    caption="Color Feed"
                )
                depth_placeholder.image(
                    depth_colormap,
                    channels="RGB",
                    use_container_width=True,
                    caption="Depth Feed"
                )
    except Exception as e:
        st.error(f"Camera error: {str(e)}")
        if 'pipe' in locals():
            pipe.stop()

if __name__ == "__main__":
    main()