import time
import subprocess
from typing import Any, Annotated, TypedDict, Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool, StructuredTool

import pyrealsense2 as rs
import numpy as np
import cv2
import base64
from openai import OpenAI
from PIL import Image
import io
from IPython.display import display, Image as IPImage, HTML
from realsensestream import ColorRealSenseStream, ColorFrame


# This is the default state same as "MessagesState" TypedDict but allows us accessibility to custom keys
class GraphsState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages] 
    # Custom keys for additional data can be added here such as - conversation_id: str

def prepare_image_for_api(image):
    # Convert numpy array to PIL Image
    pil_image = Image.fromarray(image)

    # Create a byte stream 
    byte_stream = io.BytesIO()

    # Save the image to the byte stream in JPEG format 
    pil_image.save(byte_stream, format='JPEG')

    # Get the byte value and encode to base64
    img_bytes = byte_stream.getvalue()
    base64_image = base64.b64encode(img_bytes).decode('utf-8')

    return base64_image, byte_stream.getvalue()


def analyze_image_with_openai(base64_image, prompt):
    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
             messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

# Tool to analyze image 
def capture_and_analyze_frame(prompt: str):
    """
    Uses the existing camera instance to get a frame and analyze it
    """
    try:
        # Get the existing camera instance
        camera = ColorRealSenseStream()
        
        # Get a frame
        frame_data = camera.streaming_color_frame()
        
        if frame_data.error is None:
            # Prepare the frame for API analysis
            base64_image, jpeg_bytes = prepare_image_for_api(frame_data.image)
            
            # Analyze the prepared image using OpenAI
            result = analyze_image_with_openai(base64_image, prompt)
            return result
        else:
            return f"Error capturing frame: {frame_data.error}"
            
    except Exception as e:
        return f"Error processing frame: {str(e)}"

# Tool to list usb devices 
def list_usb_devices() -> list:
    """
    Retrieves a list of all USB devices connected to the system using the lsusb command.
    
    Returns:
        list: A list of strings representing USB devices with their details
    """
    devices = []
    result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
    for line in result.stdout.strip().split('\n'):
        devices.append(line)
    return devices


# Set up tools
tools = [capture_and_analyze_frame, list_usb_devices]

# Initialize LLM 
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)


# System Message
sys_msg = SystemMessage(
    content=(
        """
        You are a helpful assistant with two primary capabilities:

    1. Vision Analysis
        You can analyze images provide insightful, detailed observations in response to user queries.
        When a vision-related question is asked, carefully examine the provided image and describe relevant features, objects, contexts, or any other notable elements.

    2. Device Management
        You can identify and manage devices connected to the system, offering precise information and instructions based on their specifications or status.
        When a device-related question is asked, reference the current list of connected devices (or relevant data) to provide appropriate guidance or details.
    Instructions

    For vision-related queries, provide clear, comprehensive image analyses.
    For device-related queries, deliver precise, actionable details that address the user’s request.
    Always strive to give concise, user-friendly, and contextually appropriate responses."""
    )
)

# Node 
def assistant(state):
    """Process messages in the state and return LLM response."""
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Graph setup 
graph = StateGraph(GraphsState)
graph.add_node("assistant", assistant)
graph.add_node("tools", ToolNode(tools))

# Define edges
graph.add_edge(START, "assistant")
graph.add_conditional_edges(
    "assistant",
    tools_condition,
)
graph.add_edge("tools", "assistant")

# Compile graph
graph_runnable = graph.compile()


def invoke_our_graph(st_messages, callables):
    # Ensure the callables parameter is a list as you can have multiple callbacks
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    # Invoke the graph with the current messages and callback configuration
    return graph_runnable.invoke({"messages": st_messages}, config={"callbacks": callables})
