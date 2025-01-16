import streamlit as st
from PIL import Image



# Image Display Container
with st.container():
    st.header("🖼️ Image Viewer")
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        # Display uploaded image
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_container_width=True)


# Chatbot Container
with st.container():
    st.header("🤖 Chatbot")
    
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    # Display previous messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    if user_input := st.chat_input("Type your message"):
        # Add user message to chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})
        
        # Generate bot response
        bot_response = f"I'm just a demo bot! You said: '{user_input}'"
        st.session_state["messages"].append({"role": "assistant", "content": bot_response})
        
        # Display bot message
        with st.chat_message("assistant"):
            st.markdown(bot_response)