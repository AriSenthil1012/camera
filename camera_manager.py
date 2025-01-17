import streamlit as st
from color_frame_stream import ColorRealSenseStream, ColorFrame
import time
import os
from datetime import datetime
import cv2
from PIL import Image
import numpy as np

def save_image(image: np.ndarray, save_dir: str = "saved_images") -> str:
    """
    Save the captured frame as an image
    
    Args:
        image: numpy array of the image
        save_dir: directory to save images
        
    Returns:
        str: path to saved image
    """
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    
    # Convert numpy array to PIL Image and save
    Image.fromarray(image).save(filepath)
    return filepath

def load_saved_images(save_dir: str = "saved_images") -> list:
    """
    Load all saved images from the directory
    
    Returns:
        list: List of image paths
    """
    if not os.path.exists(save_dir):
        return []
        
    image_files = [
        os.path.join(save_dir, f) 
        for f in os.listdir(save_dir) 
        if f.endswith(('.jpg', '.jpeg', '.png'))
    ]
    return sorted(image_files, reverse=True)  # Most recent first

def display_image_gallery(image_paths: list, cols: int = 3):
    """
    Display saved images in a grid layout
    
    Args:
        image_paths: List of paths to images
        cols: Number of columns in the grid
    """
    # Create rows based on number of images and columns
    rows = len(image_paths) // cols + (1 if len(image_paths) % cols > 0 else 0)
    
    for row in range(rows):
        # Create columns for each row
        columns = st.columns(cols)
        
        # Fill each column with an image
        for col in range(cols):
            idx = row * cols + col
            if idx < len(image_paths):
                with columns[col]:
                    img = Image.open(image_paths[idx])
                    st.image(img, use_column_width=True)
                    if st.button(f"Delete", key=f"del_{idx}"):
                        os.remove(image_paths[idx])
                        st.experimental_rerun()

def color_camera_frontend_container():
    """
    Create a Streamlit container for displaying the color camera feed
    with save functionality and image gallery.
    """
    # Create container for camera feed
    with st.container():
        frame_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Add save photo button
        save_col, status_col = st.columns([1, 4])
        with save_col:
            save_button = st.button("📸 Save Photo")
        
        # Initialize camera feed stream if not already present
        if 'camera_stream' not in st.session_state:
            st.session_state.camera_stream = ColorRealSenseStream()
            
        # Initialize last_frame in session state
        if 'last_frame' not in st.session_state:
            st.session_state.last_frame = None
        
        try:
            while True:
                # Get frame from camera
                frame_data: ColorFrame = st.session_state.camera_stream.streaming_color_frame()
                
                if frame_data.error:
                    # Display error in status
                    status_placeholder.error(f"Camera Error: {frame_data.error}")
                    time.sleep(1)
                    continue
                
                # Store current frame
                st.session_state.last_frame = frame_data.image
                
                # Display frame from the camera
                frame_placeholder.image(
                    frame_data.image,
                    channels="RGB",
                    use_container_width=True
                )
                
                # Update status
                with status_col:
                    status_placeholder.success("RealSense Camera is running...")
                
                # Check if save button was pressed
                if save_button and st.session_state.last_frame is not None:
                    saved_path = save_image(st.session_state.last_frame)
                    st.toast(f"Image saved: {os.path.basename(saved_path)}", icon="✅")
                    save_button = False  # Reset button state
                
                # Short sleep to prevent excessive CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            status_placeholder.error(f"Stream Error: {str(e)}")
            
        finally:
            # This only runs when the session ends or on error
            if 'camera_stream' in st.session_state:
                st.session_state.camera_stream.stop()
                del st.session_state.camera_stream

    # Create container for image gallery
    with st.container():
        st.markdown("### Saved Images")
        saved_images = load_saved_images()
        if saved_images:
            display_image_gallery(saved_images)
        else:
            st.info("No saved images yet. Click 'Save Photo' to capture images!")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    color_camera_frontend_container()