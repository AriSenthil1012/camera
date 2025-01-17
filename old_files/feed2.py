import streamlit as st
import os
from PIL import Image

def load_saved_images(save_dir=r"/home/ari/camera/saved_images") -> list:
    """Load all saved images from the directory"""
    if not os.path.exists(save_dir):
        return []
        
    image_files = [
        os.path.join(save_dir, f) 
        for f in os.listdir(save_dir) 
        if f.endswith(('.jpg', '.jpeg', '.png'))
    ]
    return sorted(image_files, reverse=True)  # Most recent first

def display_image_grid():
    """Display images in a scrollable grid"""
    
    # Load saved images
    saved_images = load_saved_images()
    
    if not saved_images:
        st.info("No saved images yet!")
        return

    # Create a scrollable container
    with st.container(height=400):
        # Calculate number of rows needed
        num_images = len(saved_images)
        num_rows = (num_images + 2) // 3  # Ceiling division by 3
        
        # Create rows of 3 columns each
        for row_idx in range(num_rows):
            # Create three columns for each row
            cols = st.columns(3)
            
            # Fill each column in the row
            for col_idx, col in enumerate(cols):
                # Calculate the image index
                img_idx = row_idx * 3 + col_idx
                
                # Check if we still have images to display
                if img_idx < num_images:
                    with col:
                        # Create a container for the image and buttons
                        with st.container():
                            # Load and display image
                            image = Image.open(saved_images[img_idx])
                            st.image(image, use_container_width=True)
                            
                            # Create a row for the buttons
                            btn_col1, btn_col2 = st.columns(2)
                            
                            # # Add a small spacing after each image
                            # st.markdown("<br>", unsafe_allow_html=True)

def main():
    st.title("Saved Images Gallery")
    
    # Add some styling to make the gallery look better
    st.markdown("""
        <style>
        /* Add some spacing between images */
        .stImage {
            margin-bottom: 0.5rem;
        }
        
        /* Make buttons more compact */
        .stButton button {
            padding: 0rem 1rem;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    display_image_grid()

if __name__ == "__main__":
    main()