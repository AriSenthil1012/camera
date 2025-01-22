import streamlit as st
from color_frame_stream import ColorRealSenseStream, ColorFrame
import time
import os
from datetime import datetime
import cv2
from PIL import Image
import numpy as np

def color_camera_frontend_container():
    """ 
    Create a Streamlit container for displaying the color camera feed
    """

    # Create container for camera feed 
    with st.container():
        frame_placeholder = st.empty()

        # Initalize camera feed stream if not already present 
        if 'camera_stream' not in st.session_state:
            st.session_state.camera_stream = ColorRealSenseStream()

        # Initialize last_frame in session_state 
        if 'last_frame' not in st.session_state:
            st.session_state.last_frame = None
        
        try: 
            while True:
                # Get frame from camera 
                frame_data: ColorFrame = st.session_state.camera_stream.streaming_color_frame()

                # Store current frame 
                st.session_state.last_frame = frame_data.image 

                # Display frame from the camera 
                frame_placeholder.image(
                    frame_data.image,
                    channels="RGB",
                    use_container_width=True
                )

                time.sleep(0.01)

        finally:
            # This only runs when the session ends or on error
            if 'camera_stream' in st.session_state:
                st.session_state.camera_stream.stop()
                del st.session_state.camera_stream 

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    color_camera_frontend_container()



        