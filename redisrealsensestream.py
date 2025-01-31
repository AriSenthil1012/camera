import pyrealsense2 as rs
import numpy as np
import redis
import cv2
import time
import threading
from typing import Optional
from dataclasses import dataclass
import pickle

# Initialize Redis Client (Assuming Redis is running on localhost:6379)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@dataclass
class FrameData:
    """Data structure for RealSense frames."""
    color_image: Optional[np.ndarray]
    depth_image: Optional[np.ndarray]
    timestamp: float
    error: Optional[str]

class RealSenseRedisStreamer:
    def __init__(self):
        """ Initialize RealSense camera stream and Redis storage """
        self.pipe = None
        self.config = None
        self.running = False
        self._initialize_pipeline()
        
    def _initialize_pipeline(self):
        """ Set up the RealSense pipeline """
        try:
            self.pipe = rs.pipeline()
            self.config = rs.config()

            # Enable color and depth streams
            self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
            self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

            self.pipe.start(self.config)
            self.running = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RealSense pipeline: {str(e)}")

    def _save_to_redis(self, frame_data: FrameData):
        """Serialize and store frame data in Redis"""
        try:
            # Encode color image to PNG format
            _, color_encoded = cv2.imencode('.png', frame_data.color_image)
            # Encode depth image (optional)
            _, depth_encoded = cv2.imencode('.png', frame_data.depth_image)

            # Save to Redis as a hash
            redis_client.hset("latest_frame", mapping={
                "color_image": color_encoded.tobytes(),
                "depth_image": depth_encoded.tobytes(),
                "timestamp": str(frame_data.timestamp),
                "error": frame_data.error or ""
            })
        except Exception as e:
            print(f"Error saving frame to Redis: {e}")

    def stream_frames(self):
        """ Continuously capture frames and store them in Redis """
        while self.running:
            try:
                # Wait for frames
                frames = self.pipe.wait_for_frames()
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    frame_data = FrameData(None, None, time.time(), "No frame available")
                else:
                    color_image = np.asanyarray(color_frame.get_data())
                    depth_image = np.asanyarray(depth_frame.get_data())

                    frame_data = FrameData(color_image, depth_image, time.time(), None)

                # Store in Redis
                self._save_to_redis(frame_data)

                # Reduce CPU load
                time.sleep(0.03)  # Approx 30 FPS
            except Exception as e:
                print(f"Error capturing frames: {e}")
                self.running = False

    def stop(self):
        """ Stop RealSense pipeline """
        self.running = False
        if self.pipe:
            self.pipe.stop()
        print("RealSense Streaming Stopped.")

