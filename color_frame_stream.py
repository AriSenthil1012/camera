import pyrealsense2 as rs 
import numpy as np 
from typing import Optional, Tuple 
from dataclasses import dataclass

@dataclass 
class ColorFrame:
    """ Data class to hold color frame data"""
    image: np.ndarray
    error: Optional[str] = None 

class ColorRealSenseStream:
    def __init__(self):
        """ Initialize RealSense camera stream"""
        self.pipe = None
        self.config = None 
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Set up the RealSense pipeline"""
        try: 
            self.pipe = rs.pipeline()
            self.config = rs.config()

            # Enable the color stream
            self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
            self.pipe.start(self.config)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize RealSense pipeline: {str(e)}")
        
    def streaming_color_frame(self) -> ColorFrame:
        """
        Get the latest color frame from the RealSense camera. 
        
        Returns:
            ColorFrame: Object containing the image data and metadata 
        """

        try: 
            # Wait for the next set of frames 
            frames = self.pipe.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                return ColorFrame(image=np.zeros((720, 1280, 3), dtype=np.uint8), 
                                  error="No color frame available")
            
            # Convert frame to numpy array 
            color_image = np.asanyarray(color_frame.get_data())

            return ColorFrame(image=color_image, 
                              error=None)
        
        except Exception as e:
            return ColorFrame(
                image=np.zeros((720, 1280, 3), dtype=np.uint8),
                error=f"Error capturing color frame (RGB8): {str(e)}")
        
    def stop(self):
        """Stop the RealSense pipeline"""
        if self.pipe:
            self.pipe.stop()

