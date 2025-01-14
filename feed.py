import streamlit as st
import pyrealsense2 as rs
import numpy as np
import cv2

def main():
    st.title("RealSense Live Feed")
    
    # Initialize the RealSense pipeline
    pipe = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    # Create a placeholder for the video feed
    frame_placeholder = st.empty()
    
    # Start the pipeline
    profile = pipe.start(config)
    
    try:
        while True:
            # Wait for the next set of frames
            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue
                
            # Convert frame to numpy array
            color_image = np.asanyarray(color_frame.get_data())
            
            # Convert BGR to RGB
            color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            
            # Display the frame
            frame_placeholder.image(color_image, channels="RGB", use_container_width=True)
            
    finally:
        pipe.stop()

if __name__ == "__main__":
    main()