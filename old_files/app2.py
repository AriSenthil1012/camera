import os
import streamlit.components.v1 as components
import streamlit as st
from dotenv import load_dotenv
import pyrealsense2 as rs
import numpy as np
import cv2
from langchain_core.messages import AIMessage, HumanMessage
from graph import invoke_our_graph
from st_callable_util import get_streamlit_cb
import threading
import base64
from io import BytesIO
import time

class CameraComponent:
    def __init__(self):
        self.pipe = None
        self.is_running = False
        self._setup_pipeline()

    def _setup_pipeline(self):
        self.pipe = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipe.start(config)

    def _process_frame(self):
        frames = self.pipe.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        
        if not color_frame or not depth_frame:
            return None, None
        
        # Process color frame
        color_image = np.asanyarray(color_frame.get_data())
        color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        
        # Process depth frame
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )
        depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)
        
        return color_image, depth_colormap

    def _frame_to_base64(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def _generate_html(self, color_b64, depth_b64):
        return f"""
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <div>
                <h4 style="margin: 0;">Color Feed</h4>
                <img src="data:image/jpeg;base64,{color_b64}" style="width: 100%;" />
            </div>
            <div>
                <h4 style="margin: 0;">Depth Feed</h4>
                <img src="data:image/jpeg;base64,{depth_b64}" style="width: 100%;" />
            </div>
        </div>
        """

    def camera_component(self):
        if not hasattr(st.session_state, 'camera_html'):
            st.session_state.camera_html = components.html(
                self._generate_html('', ''),
                height=800
            )
        
        while True:
            try:
                color_frame, depth_frame = self._process_frame()
                if color_frame is not None and depth_frame is not None:
                    color_b64 = self._frame_to_base64(color_frame)
                    depth_b64 = self._frame_to_base64(depth_frame)
                    st.session_state.camera_html.html(
                        self._generate_html(color_b64, depth_b64)
                    )
                    time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                st.error(f"Camera error: {str(e)}")
                break

    def __del__(self):
        if self.pipe:
            self.pipe.stop()

def main():
    st.set_page_config(layout="wide")
    load_dotenv()

    # Create the basic two-column layout
    left_col, right_col = st.columns([0.7, 0.3])

    # Initialize camera component in session state
    if 'camera' not in st.session_state:
        st.session_state.camera = CameraComponent()

    # Left column - Camera feeds
    with left_col:
        if st.button("Start/Stop Camera"):
            if not hasattr(st.session_state, 'camera_thread'):
                camera_thread = threading.Thread(
                    target=st.session_state.camera.camera_component,
                    daemon=True
                )
                st.session_state.camera_thread = camera_thread
                camera_thread.start()
            else:
                del st.session_state.camera_thread

    # Right column - Chat interface
    with right_col:
        st.header("Chat")
        if "messages" not in st.session_state:
            st.session_state["messages"] = [AIMessage(content="How can I help you?")]

        # Display chat messages
        for msg in st.session_state.messages:
            if isinstance(msg, AIMessage):
                st.chat_message("assistant").write(msg.content)
            elif isinstance(msg, HumanMessage):
                st.chat_message("user").write(msg.content)

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.messages.append(HumanMessage(content=prompt))
            st.chat_message("user").write(prompt)

            msg_placeholder = st.empty()
            stream_placeholder = st.empty()
            
            with stream_placeholder:
                with st.spinner("AI is thinking..."):
                    st_callback = get_streamlit_cb(stream_placeholder)
                    try:
                        response = invoke_our_graph(st.session_state.messages, [st_callback])
                        last_msg = response["messages"][-1].content
                        st.session_state.messages.append(AIMessage(content=last_msg))
                        msg_placeholder.write(last_msg)
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        stream_placeholder.empty()

if __name__ == "__main__":
    main()