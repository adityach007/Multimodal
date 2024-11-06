import streamlit as st
from llm_chains import load_normal_chain, load_pdf_chat_chain
from langchain.memory import StreamlitChatMessageHistory
from streamlit_mic_recorder import mic_recorder
from utils import save_chat_history_json, get_timestamp, load_chat_history_json
from image_handler import handle_image
from audio_handler import transcribe_audio
from pdf_handler import add_documents_to_db
from html_templates import get_bot_template, get_user_template, css
from dotenv import load_dotenv
import yaml
import os
import time
from datetime import datetime

# Load environment variables and configuration
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

AVAILABLE_MODELS = [
    "gemma2-9b-it",
    "gemma-7b-it",
    "llama3-groq-70b-8192-tool-use-preview",
    "llama3-groq-8b-8192-tool-use-preview",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-guard-3-8b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768"
]

def load_chain(chat_history):
    model_name = st.session_state.selected_model
    if st.session_state.pdf_chat:
        print("loading pdf chat chain")
        return load_pdf_chat_chain(chat_history, model_name=model_name)
    return load_normal_chain(chat_history, model_name=model_name)

def clear_input_field():
    if st.session_state.user_question == "":
        st.session_state.user_question = st.session_state.user_input
        st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()

def toggle_pdf_chat():
    st.session_state.pdf_chat = True

def save_chat_history():
    if st.session_state.history != []:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp() + ".json"
            save_chat_history_json(st.session_state.history, config["chat_history_path"] + st.session_state.new_session_key)
        else:
            save_chat_history_json(st.session_state.history, config["chat_history_path"] + st.session_state.session_key)

def display_chat_history(messages, thinking_steps_history):
    """Display complete chat history with thinking steps."""
    for i, message in enumerate(messages):
        timestamp = datetime.fromtimestamp(message.additional_kwargs.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
        
        if message.type == "human":
            st.write(get_user_template(message.content, timestamp), unsafe_allow_html=True)
        else:
            # Get thinking steps for this message if available
            steps = thinking_steps_history.get(i, None)
            st.write(get_bot_template(message.content, timestamp, steps), unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Multimodal Chat with Groq", page_icon="🤖", layout="wide")
    st.title("Multimodal Chat App with Groq Integration")
    st.write(css, unsafe_allow_html=True)
    
    # Initialize session states
    if "send_input" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
        st.session_state.thinking_steps_history = {}
        st.session_state.current_thinking_steps = []
        st.session_state.message_timestamps = {}  # New: store timestamps separately
        st.session_state.pdf_chat = False

    # Groq status indicator
    with st.sidebar:
        st.write("🤖 Using Groq API")
        if not os.getenv("GROQ_API_KEY"):
            st.error("⚠️ GROQ_API_KEY not found in environment variables")
        
        # Initialize selected_model in session state if not present
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "llama-3.1-70b-versatile"
        
        st.session_state.selected_model = st.selectbox(
            "Select Model",
            options=AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.selected_model)
        )
    
    # Chat session management
    st.sidebar.title("Chat Sessions")
    chat_sessions = ["new_session"] + sorted(os.listdir(config["chat_history_path"]))
    
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key is not None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

    index = chat_sessions.index(st.session_state.session_index_tracker)
    selected_session = st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index)
    
    # PDF chat toggle
    st.sidebar.toggle("PDF Chat", key="pdf_chat", value=False)

    # Load chat history
    if selected_session != "new_session":
        st.session_state.history = load_chat_history_json(config["chat_history_path"] + selected_session)
    else:
        st.session_state.history = []

    chat_history = StreamlitChatMessageHistory(key="history")
    
    # Main layout
    chat_container = st.container()
    thinking_container = st.container()
    input_container = st.container()

    # File upload section in sidebar
    with st.sidebar:
        st.title("Upload Files")
        uploaded_audio = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])
        uploaded_image = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])
        uploaded_pdf = st.file_uploader(
            "Upload a pdf file", 
            accept_multiple_files=True, 
            key="pdf_upload", 
            type=["pdf"], 
            on_change=toggle_pdf_chat
        )

    # Process uploaded files
    if uploaded_pdf:
        with st.spinner("Processing PDF..."):
            add_documents_to_db(uploaded_pdf)

    if uploaded_audio:
        with st.spinner("Transcribing audio..."):
            transcribed_audio = transcribe_audio(uploaded_audio.getvalue())
            llm_chain = load_chain(chat_history)
            response = llm_chain.run("Summarize this text: " + transcribed_audio)
            current_time = time.time()
            
            # Store timestamp before adding message
            message_index = len(chat_history.messages)
            st.session_state.message_timestamps[message_index] = current_time
            chat_history.add_user_message("Audio transcription: " + transcribed_audio)
            
            st.session_state.message_timestamps[message_index + 1] = current_time
            chat_history.add_ai_message(response)

    # Input section
    with input_container:
        user_input = st.text_input("Type your message here", key="user_input", on_change=set_send_input)
        col1, col2 = st.columns(2)
        with col1:
            voice_recording = mic_recorder(
                start_prompt="Start recording",
                stop_prompt="Stop recording",
                just_once=True
            )
        with col2:
            send_button = st.button("Send", key="send_button", on_click=clear_input_field)

    # Handle voice recording
    if voice_recording:
        with st.spinner("Processing voice recording..."):
            transcribed_audio = transcribe_audio(voice_recording["bytes"])
            llm_chain = load_chain(chat_history)
            response = llm_chain.run(transcribed_audio)
            current_time = time.time()
            
            message_index = len(chat_history.messages)
            st.session_state.message_timestamps[message_index] = current_time
            chat_history.add_user_message("Voice input: " + transcribed_audio)
            
            st.session_state.message_timestamps[message_index + 1] = current_time
            chat_history.add_ai_message(response)

    # Process user input and generate response
    if send_button or st.session_state.send_input:
        current_time = time.time()
        
        # Handle command execution
        if st.session_state.user_question.startswith("!cmd "):
            command = st.session_state.user_question[5:]
            llm_chain = load_chain(chat_history)
            response = llm_chain.llm.execute_command(command)
            message_index = len(chat_history.messages)
            st.session_state.message_timestamps[message_index] = current_time
            chat_history.add_user_message(command)
            st.session_state.message_timestamps[message_index + 1] = current_time
            chat_history.add_ai_message(response)
            st.session_state.user_question = ""
        
        # Handle image analysis
        if uploaded_image:
            with st.spinner("Processing image..."):
                user_message = "Describe this image in detail please."
                if st.session_state.user_question:
                    user_message = st.session_state.user_question
                    st.session_state.user_question = ""
                
                llm_answer = handle_image(uploaded_image.getvalue(), user_message)
                message_index = len(chat_history.messages)
                st.session_state.message_timestamps[message_index] = current_time
                chat_history.add_user_message(user_message)
                
                st.session_state.message_timestamps[message_index + 1] = current_time
                chat_history.add_ai_message(llm_answer)

        # Handle text input
        if st.session_state.user_question:
            user_message = st.session_state.user_question
            message_index = len(chat_history.messages)
            st.session_state.message_timestamps[message_index] = current_time
            chat_history.add_user_message(user_message)
            
            llm_chain = load_chain(chat_history)
            current_steps = []
            
            # Process and display thinking steps
            with thinking_container:
                thinking_status = st.empty()
                response_placeholder = st.empty()
                
                for step_num, (title, content, thinking_time) in enumerate(
                    llm_chain.run_with_steps(user_message), 1
                ):
                    if "Final Answer" not in title:
                        current_steps.append((title, content))
                        thinking_status.markdown(f"🤔 Step {step_num}: {title}")
                        with response_placeholder.container():
                            st.markdown(f"**{title}**")
                            st.markdown(content)
                            st.markdown(f"*Thinking time: {thinking_time:.2f}s*")
                    else:
                        # Store final answer and thinking steps
                        message_index = len(chat_history.messages)
                        st.session_state.message_timestamps[message_index] = time.time()
                        chat_history.add_ai_message(content)
                        st.session_state.thinking_steps_history[message_index] = current_steps
            
            st.session_state.user_question = ""
        
        st.session_state.send_input = False

    # Modified display_chat_history function
    def display_chat_history(messages, thinking_steps_history):
        """Display complete chat history with thinking steps."""
        for i, message in enumerate(messages):
            timestamp = datetime.fromtimestamp(
                st.session_state.message_timestamps.get(i, time.time())
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            if message.type == "human":
                st.write(get_user_template(message.content, timestamp), unsafe_allow_html=True)
            else:
                steps = thinking_steps_history.get(i, None)
                st.write(get_bot_template(message.content, timestamp, steps), unsafe_allow_html=True)

    # Display chat history
    with chat_container:
        st.markdown("### Chat History")
        if chat_history.messages:
            display_chat_history(chat_history.messages, st.session_state.thinking_steps_history)
        else:
            st.info("Start a conversation by typing a message or uploading a file.")

    # Add scroll to top button
    st.markdown('''
        <button onclick="window.scrollTo(0,0)" class="scroll-top-btn">↑</button>
    ''', unsafe_allow_html=True)
    
    # Save chat history
    save_chat_history()

if __name__ == "__main__":
    main()