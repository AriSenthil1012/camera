# streamlit_app.py
import streamlit as st
from camera_manager import CameraManager
import time

def color_camera_frontend_container():
    # Initialize camera manager in session state if not exists
    if 'camera_manager' not in st.session_state:
        st.session_state.camera_manager = CameraManager()

    with st.container():
        # Camera controls
        col1, col2 = st.columns([3, 1])
        with col2:
            camera_enabled = st.toggle('Enable Camera', value=False)

        # Display container
        with col1:
            frame_placeholder = st.empty()
            status_placeholder = st.empty()

        if camera_enabled:
            st.session_state.camera_manager.start()
            try:
                while camera_enabled:
                    frame = st.session_state.camera_manager.get_next_frame()
                    if frame is not None:
                        frame_placeholder.image(
                            frame,
                            channels="RGB",
                            use_container_width=True
                        )
                        status_placeholder.success("RealSense Camera is running...")
                    else:
                        status_placeholder.error("Failed to get frame")
                    time.sleep(0.01)
            except Exception as e:
                status_placeholder.error(f"Stream Error: {str(e)}")
            finally:
                if not camera_enabled:
                    st.session_state.camera_manager.stop()
                    frame_placeholder.empty()
                    status_placeholder.empty()


def main():
    st.title("Camera Frontend")
    color_camera_frontend_container()

if __name__ == "__main__":
    main()