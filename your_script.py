import streamlit as st
from streamlit_elements import elements, dashboard, mui, html
from color_frame_stream import ColorRealSenseStream, ColorFrame
import time

def init_camera():
    """Initialize the camera if not already initialized"""
    if 'camera_stream' not in st.session_state:
        st.session_state.camera_stream = ColorRealSenseStream()
    if 'current_frame' not in st.session_state:
        st.session_state.current_frame = None

def dashboard_camera():
    """Create a draggable dashboard with camera feed"""
    # Set wide layout
    st.set_page_config(layout="wide")
    
    # Initialize camera
    init_camera()
    
    # Create a frame for elements
    with elements("dashboard"):
        # Layout configuration
        layout = [
            # Parameters: x, y, width, height, id
            dashboard.Item("camera", 0, 0, 6, 4),
        ]
        
        # Create dashboard
        with dashboard.Grid(layout):
            # Camera feed item
            with mui.Paper(key="camera", 
                         sx={
                             "display": "flex",
                             "flexDirection": "column",
                             "borderRadius": 3,
                             "overflow": "hidden",
                         }):
                with mui.Box(sx={
                    "p": 2,
                    "borderBottom": 1,
                    "borderColor": "divider",
                    "backgroundColor": "primary.main"
                }):
                    mui.Typography("RealSense Camera Feed", 
                                 color="white",
                                 variant="h6")
                
                # Camera feed container
                with mui.Box(sx={
                    "flex": 1,
                    "minHeight": 0,
                    "overflow": "hidden",
                    "p": 2,
                    "backgroundColor": "#000000"
                }):
                    try:
                        # Get frame from camera
                        frame_data = st.session_state.camera_stream.streaming_color_frame()
                        
                        if frame_data.error:
                            mui.Typography(
                                f"Camera Error: {frame_data.error}",
                                color="error",
                                align="center"
                            )
                        else:
                            # Convert frame to base64 for display
                            from PIL import Image
                            import io
                            import base64
                            
                            # Convert numpy array to PIL Image
                            image = Image.fromarray(frame_data.image)
                            
                            # Convert to base64
                            buffered = io.BytesIO()
                            image.save(buffered, format="JPEG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            
                            # Display using HTML img tag
                            html.img(
                                src=f"data:image/jpeg;base64,{img_str}",
                                css={
                                    "width": "100%",
                                    "height": "100%",
                                    "objectFit": "contain"
                                }
                            )
                            
                    except Exception as e:
                        mui.Typography(
                            f"Stream Error: {str(e)}",
                            color="error",
                            align="center"
                        )

if __name__ == "__main__":
    dashboard_camera()