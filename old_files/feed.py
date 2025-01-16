import streamlit as st
import pyrealsense2 as rs
import numpy as np
import cv2

def main():    
    # Initialize the RealSense pipeline
    pipe = rs.pipeline()
    config = rs.config()
    
    # Enable both color and depth streams
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    
    # Create placeholders for both video feeds
    color_frame_placeholder = st.empty()
    depth_frame_placeholder = st.empty()
    
    # Start the pipeline
    profile = pipe.start(config)
    
    # Get depth scale for converting depth values to meters
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    
    try:
        while True:
            # Wait for the next set of frames
            frames = pipe.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                continue
                
            # Convert frames to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # Convert BGR to RGB for color image
            color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            
            # Apply colormap to depth image for better visualization
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03), 
                cv2.COLORMAP_JET
            )
            depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)
            
            # Display both frames
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
            
    finally:
        pipe.stop()

if __name__ == "__main__":
    main()