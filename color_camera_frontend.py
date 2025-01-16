import streamlit as st 
from color_frame_stream import ColorRealSenseStream, ColorFrame
import time 

class CameraManager:
    def __init__(self):
        self.current_frame = None
        self.camera_stream = None

    def update_frame(self,frame):
        self.current_frame = frame 

    def get_current_frame(self):
        return self.current_frame


def color_camera_frontend_container(camera_manager):
    """
    Create a Streamlit container for displaying the color camera feed.
    This function handles only the frontend display logic 
    """

    # Create container for camera feed 
    with st.container():
        
        frame_placeholder = st.empty()

        status_placeholder = st.empty()

        # Initialize camera feed stream if not already present 
        if camera_manager.camera_stream is None:
            camera_manager.camera_stream = ColorRealSenseStream()

        try: 
            while True:
                # Get frame from camera
                frame_data: ColorFrame = camera_manager.camera_stream.streaming_color_frame()

                if frame_data.error:
                    # Display error in status 
                    status_placeholder.error(f"Camera Error: {frame_data.error}")
                    time.sleep(1)
                    continue
                
                # Store the frame in the manager 
                camera_manager.update_frame(frame_data.image)
                
                # Display from the camera 
                frame_placeholder.image(
                    frame_data.image,
                    channels="RGB",
                    use_container_width=True
                )

                # Update status 
                status_placeholder.success("RealSense Camera is running...")

                # Short sleep to prevent excessive CPU usage 
                time.sleep(0.01)

        except Exception as e:
            status_placeholder.error(f"Stream Error: {str(e)}")

        finally:
            # This only runs when the session ends or on error
            if 'camera_stream' in st.session_state:
                st.session_state.camera_stream.stop()
                del st.session_state.camera_stream


def process_frame(camera_manager):
    current_frame = camera_manager.get_current_frame()

    if current_frame is not None:
        return current_frame 
    
    return None



        