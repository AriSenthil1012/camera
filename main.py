import streamlit as st
from color_camera_frontend import color_camera_frontend_container, CameraManager, process_frame

def main():
    st.set_page_config(
        page_title="RealSense Camera Stream",
        layout="wide"
    )

    # Run the camera container  and the camera manager
    camera_manager = CameraManager()
    color_camera_frontend_container(camera_manager)
    process_frame(camera_manager)

if __name__ == "__main__":
    main()