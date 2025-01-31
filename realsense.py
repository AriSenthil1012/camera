import pyrealsense2 as rs
import numpy as np
from typing import Optional
from dataclasses import dataclass
import threading
import queue
import time
import io
import base64
from PIL import Image
import psycopg2
from contextlib import contextmanager

@dataclass
class Frame:
    """Data class to hold frame data"""
    color_image: np.ndarray
    depth_image: np.ndarray
    error: Optional[str] = None

    def encode_color_image(self) -> str:
        """Convert numpy color image to Base64 string"""
        pil_image = Image.fromarray(self.color_image)
        byte_stream = io.BytesIO()
        pil_image.save(byte_stream, format='JPEG')
        img_bytes = byte_stream.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')

    def encode_depth_image(self) -> bytes:
        """Convert numpy depth image to BLOB (binary)"""
        depth_bytes = io.BytesIO()
        np.save(depth_bytes, self.depth_image, allow_pickle=False)
        return depth_bytes.getvalue()

class DatabaseConnection:
    def __init__(self, dbname="postgres", user="postgres", 
                 password="1012", host="localhost", port="5432"):
        self.connection_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
        finally:
            conn.close()

    def insert_frame(self, frame: Frame, timestamp: int):
        """Insert a Frame into TimescaleDB"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            color_image_base64 = frame.encode_color_image()
            depth_image_blob = frame.encode_depth_image()
            
            cursor.execute(
                "INSERT INTO frames (timestamp, color_image_base64, depth_image) "
                "VALUES (%s, %s, %s)",
                (timestamp, color_image_base64, psycopg2.Binary(depth_image_blob))
            )
            conn.commit()

class RealSenseStream:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RealSenseStream, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_config=None):
        if self._initialized:
            return
        
        # Initialize database connection
        if db_config is None:
            db_config = {}
        self.db = DatabaseConnection(**db_config)
        
        self.pipe = None
        self.config = None
        self.frame_queue = queue.Queue(maxsize=1)
        self.is_running = False
        self._initialize_pipeline()
        self._initialized = True

    def _initialize_pipeline(self):
        """Set up the RealSense pipeline with both depth and color streams"""
        try:
            self.pipe = rs.pipeline()
            self.config = rs.config()

            # Configure depth and color streams
            self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
            self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)

            # Get device and configure depth settings
            pipeline_wrapper = rs.pipeline_wrapper(self.pipe)
            pipeline_profile = self.config.resolve(pipeline_wrapper)
            device = pipeline_profile.get_device()
            depth_sensor = device.first_depth_sensor()

            # Enable emitter
            if depth_sensor.supports(rs.option.emitter_enabled):
                depth_sensor.set_option(rs.option.emitter_enabled, 1)

            # Set laser power
            if depth_sensor.supports(rs.option.laser_power):
                max_power = depth_sensor.get_option_range(rs.option.laser_power).max
                depth_sensor.set_option(rs.option.laser_power, max_power)

            # Start pipeline with config
            self.pipe.start(self.config)

            # Skip first few frames to allow auto-exposure
            for _ in range(5):
                self.pipe.wait_for_frames()

            self.is_running = True
            
            # Start frame capture thread
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize RealSense pipeline: {str(e)}")

    def _capture_frames(self):
        """Continuously capture both color and depth frames in a separate thread"""
        while self.is_running:
            try:
                frames = self.pipe.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()

                if depth_frame and color_frame:
                    depth_image = np.asanyarray(depth_frame.get_data())
                    color_image = np.asanyarray(color_frame.get_data())

                    try:
                        if not self.frame_queue.empty():
                            self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(Frame(
                            color_image=color_image,
                            depth_image=depth_image
                        ))
                    except queue.Full:
                        pass

            except Exception as e:
                if self.is_running:
                    print(f"Error capturing frame: {str(e)}")

    def get_frames(self, store_in_db: bool = True) -> Optional[Frame]:
        """
        Get the latest color and depth frames
        Args:
            store_in_db: If True, stores the frame in the database
        Returns:
            Frame object if successful, None if no frames are available
        """
        try:
            frame = self.frame_queue.get(timeout=1.0)
            
            # Store frame in database if requested
            if store_in_db:
                try:
                    timestamp = int(time.time() * 1000)  # Current time in milliseconds
                    self.db.insert_frame(frame, timestamp)
                except Exception as e:
                    print(f"Error storing frame in database: {str(e)}")
                    frame.error = f"Database storage error: {str(e)}"
            
            return frame
            
        except queue.Empty:
            return None

    def stop(self):
        """Stop the RealSense pipeline"""
        self.is_running = False
        if self.pipe:
            self.pipe.stop()
        self._initialized = False


# Usage example:
if __name__ == "__main__":
    try:
        stream = RealSenseStream()

        # Get some frames
        for _ in range(30):  # Capture 30 frames
            frames = stream.get_frames(store_in_db=True)  # Will store in database by default
            if frames.error:
                print(f"Error: {frames.error}")
            else:
                print(f"Received frame - Color shape: {frames.color_image.shape}, "
                      f"Depth shape: {frames.depth_image.shape}")

    finally:
        # Make sure to stop the stream
        stream.stop()