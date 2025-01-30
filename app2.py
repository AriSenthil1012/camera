import os
from dotenv import load_dotenv
import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage
from graph import invoke_our_graph
from realsensestream import ColorRealSenseStream, ColorFrame

# Load environment variables
load_dotenv()

# Initialize camera stream
camera_stream = ColorRealSenseStream()

# Chat history
chat_history = [AIMessage(content="Hello!")]

# Function to handle AI chat logic
def handle_chat(user_input):
    global chat_history
    # Add user message to chat history
    chat_history.append(HumanMessage(content=user_input))
    
    # Process AI response
    response = invoke_our_graph(chat_history, [])
    latest_response = response["messages"][-1].content
    
    # Add AI response to chat history
    chat_history.append(AIMessage(content=latest_response))
    return [(msg.content, "assistant" if isinstance(msg, AIMessage) else "user") for msg in chat_history]

# Function to capture camera frames for streaming
def detection():
    try:
        # Capture frame from camera
        frame_data: ColorFrame = camera_stream.streaming_color_frame()
        return frame_data.image
    except Exception as e:
        return f"Camera stream error: {str(e)}"

# Define Gradio components
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            chat = gr.Chatbot(label="Chat Interface", type="messages")
            user_input = gr.Textbox(placeholder="Type your message...", label="Input")
            user_input.submit(handle_chat, user_input, chat)
        with gr.Column():
            image = gr.Image(label="Camera Feed", type="numpy")
            
            # Use the stream method for real-time updates
            image.stream(
                fn=detection,  # The function to stream data
                inputs=None,  # No inputs required for this case
                outputs=image,  # Update the same image component
                time_limit=10  # Stream updates continuously for 10 seconds (can be adjusted)
            )

# Clean up on app closure
def on_close():
    camera_stream.stop()

# Launch the app
demo.launch()
