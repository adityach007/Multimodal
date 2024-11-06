# llm_chains.py

import groq
import json
import time
from langchain.chains import LLMChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Chroma
import chromadb
import yaml
from dotenv import load_dotenv
import os
from typing import List, Tuple, Dict, Generator, Optional
import subprocess
import pyautogui
import time
from PIL import ImageGrab
import webbrowser
import keyboard
from langchain_community.tools import DuckDuckGoSearchRun
import re

# Load environment variables and configuration
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

SYSTEM_PROMPT = """You are an expert AI assistant with advanced reasoning capabilities. 
You must respond in JSON format following this structure:
{
    "title": "Your step title or phase description",
    "content": "Your detailed explanation",
    "next_action": "continue OR final_answer",
    "confidence": "0-100 percentage indicating confidence in this step"
}

Guidelines for your response:
1. Break down complex problems into clear steps
2. Evaluate multiple perspectives and approaches
3. Consider context from conversation history
4. Acknowledge uncertainties and limitations
5. Provide evidence and reasoning for conclusions
6. Quantify confidence levels when possible

If analyzing specific content (images, documents, audio):
- Explicitly reference the content
- Describe relevant features and details
- Connect observations to conclusions

Remember: Always format responses as valid JSON."""

SIMPLE_SYSTEM_PROMPT = """You are an expert AI assistant providing clear and concise responses.
Respond in JSON format:
{
    "title": "Response Title",
    "content": "Your detailed answer",
    "confidence": "0-100 confidence score"
}"""

def web_search(query: str, num_results: int = 3) -> str:
    """
    Perform a web search using DuckDuckGo via LangChain.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        String containing formatted search results
    """
    try:
        search_tool = DuckDuckGoSearchRun()
        results = search_tool.invoke(query)
        
        if not results:
            return "No web search results found."
            
        return f"Web Search Results:\n{results}"
    
    except Exception as e:
        return f"Web search error: {str(e)}. Proceeding with AI knowledge only."

class GroqLLM:
    """
    Handles interactions with the Groq API, including retry logic and response formatting.
    """
    
    def __init__(self, model_name: str = "llama-3.1-70b-versatile", retry_attempts: int = 3, retry_delay: int = 1):
        """
        Initialize the GroqLLM instance.
        
        Args:
            model_name: Name of the model to use
            retry_attempts: Number of times to retry failed API calls
            retry_delay: Delay in seconds between retries
        """
        self.client = groq.Groq()
        self.model_name = model_name
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    def make_api_call(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 5000,  # Increased from 1000
        temperature: float = 0.3,
        stream: bool = False
    ) -> Dict:
        """
        Make an API call to Groq with retry logic.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            stream: Whether to stream the response
            
        Returns:
            Dict containing the response content
        """
        for attempt in range(self.retry_attempts):
            try:
                # Force JSON completion format only for non-streaming responses
                format_config = {"type": "json_object"} if not stream else None
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format=format_config,
                    stream=stream
                )
                
                if stream:
                    return response
                
                try:
                    # Try to parse JSON response
                    content = response.choices[0].message.content
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If JSON parsing fails, wrap the response in a valid JSON format
                    return {
                        "title": "Response",
                        "content": content,
                        "next_action": "final_answer",
                        "confidence": 50
                    }
                
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    error_msg = str(e)
                    if "Failed to generate JSON" in error_msg:
                        # Extract the failed generation if available
                        try:
                            error_data = json.loads(error_msg.split("failed_generation': '")[1].rsplit("'}", 1)[0])
                            return error_data
                        except:
                            pass
                    
                    return {
                        "title": "Error",
                        "content": f"API call failed after {self.retry_attempts} attempts: {error_msg}",
                        "next_action": "final_answer",
                        "confidence": 0
                    }
                time.sleep(self.retry_delay)

    def generate_response_with_steps(
        self,
        prompt: str,
        history: Optional[List] = None
    ) -> Generator[Tuple[str, str, float], None, None]:
        """
        Generate a step-by-step response to the prompt with web search integration.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Check if prompt needs web search (contains question words or search indicators)
        needs_web_search = bool(re.search(
            r'\b(what|how|who|when|where|why|which|search|find|lookup|latest|current|news|update|today|now)\b',
            prompt.lower()
        ))
        
        if needs_web_search:
            web_results = web_search(prompt)
            formatted_prompt = f"""Web search results for the query:

{web_results}

Based on the above web search results and your knowledge, please analyze this request and respond step-by-step:

{prompt}

Format each step as:
{{
    "title": "Current step description",
    "content": "Detailed explanation",
    "next_action": "continue OR final_answer",
    "confidence": "0-100 confidence score"
}}"""
        else:
            formatted_prompt = f"""Analyze this request and respond step-by-step:

{prompt}

Format each step as:
{{
    "title": "Current step description",
    "content": "Detailed explanation",
    "next_action": "continue OR final_answer",
    "confidence": "0-100 confidence score"
}}"""
        
        if history:
            for msg in history:
                role = "assistant" if msg.type == "ai" else "user"
                messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": formatted_prompt})
        
        step_count = 1
        while True:
            start_time = time.time()
            step_data = self.make_api_call(messages, max_tokens=2000)  # Increased from 300
            thinking_time = time.time() - start_time
            
            confidence_str = f" (Confidence: {step_data.get('confidence', 'N/A')}%)"
            step_title = step_data['title'] + confidence_str
            
            yield (step_title, step_data['content'], thinking_time)
            messages.append({"role": "assistant", "content": json.dumps(step_data)})
            
            if step_data['next_action'] == 'final_answer':
                break
                
            step_count += 1
        
        final_prompt = """Provide a final, comprehensive answer based on the previous steps.
        Format as JSON:
        {
            "title": "Final Answer",
            "content": "Your complete response",
            "next_action": "final_answer",
            "confidence": "Overall confidence score (0-100)"
        }"""
        
        messages.append({"role": "user", "content": final_prompt})
        final_data = self.make_api_call(messages, max_tokens=5000)  # Increased from 500
        yield ("Final Answer", final_data['content'], time.time() - start_time)

    def generate_simple_response(
        self,
        prompt: str,
        history: Optional[List] = None,
        max_tokens: int = 5000  # Increased from 500
    ) -> str:
        """
        Generate a simple response without step-by-step reasoning.
        
        Args:
            prompt: User's input prompt
            history: Optional conversation history
            max_tokens: Maximum tokens in response
            
        Returns:
            String containing the response content
        """
        messages = [
            {"role": "system", "content": SIMPLE_SYSTEM_PROMPT}
        ]
        
        if history:
            for msg in history:
                role = "assistant" if msg.type == "ai" else "user"
                messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.make_api_call(messages, max_tokens=max_tokens)
        return response.get('content', 'Error generating response')

    def execute_command(self, command: str) -> str:
        """
        Execute commands to control the local computer and web interactions.
        """
        try:
            parts = command.split(' ', 2)
            action = parts[0]

            # Web browser commands
            if action == 'start' and parts[1] == 'chrome':
                # Extract URL and optional parameters
                if len(parts) > 2:
                    params = parts[2].split(' -')
                    url = params[0]
                    text = None
                    new_tab = True
                    
                    for param in params[1:]:
                        if param.startswith('text '):
                            text = param[5:]
                        elif param == 'same_tab':
                            new_tab = False
                        elif param == 'incognito':
                            chrome_cmd = f'start chrome --incognito {url}'
                            subprocess.run(chrome_cmd, shell=True)
                            return f"Opened Chrome in incognito mode: {url}"
                    
                    if new_tab:
                        chrome_cmd = f'start chrome {url}'
                        subprocess.run(chrome_cmd, shell=True)
                    else:
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(0.5)
                        pyautogui.hotkey('alt', 'd')
                        time.sleep(0.5)
                        pyautogui.write(url)
                        pyautogui.press('enter')
                    
                    time.sleep(3)
                    if text:
                        pyautogui.write(text)
                        pyautogui.press('enter')
                    return f"Opened Chrome {'in new tab' if new_tab else 'in same tab'}: {url}"
                return "Please provide a URL"

            # Application control
            elif action == 'app':
                if len(parts) < 2:
                    return "Please specify an application"
                
                app_cmd = parts[1]
                if app_cmd == 'notepad':
                    subprocess.run('notepad.exe', shell=True)
                    if len(parts) > 2:
                        time.sleep(1)
                        pyautogui.write(parts[2])
                    return "Opened Notepad"
                elif app_cmd in ['calc', 'mspaint', 'cmd', 'excel', 'word', 'powerpnt']:
                    subprocess.run(f'start {app_cmd}', shell=True)
                    return f"Opened {app_cmd}"

            # Window control
            elif action == 'window':
                if len(parts) < 2:
                    return "Please specify a window action"
                
                win_cmd = parts[1]
                if win_cmd == 'minimize':
                    pyautogui.hotkey('win', 'down')
                elif win_cmd == 'maximize':
                    pyautogui.hotkey('win', 'up')
                elif win_cmd == 'switch':
                    pyautogui.hotkey('alt', 'tab')
                elif win_cmd == 'close':
                    pyautogui.hotkey('alt', 'f4')
                return f"Window {win_cmd} command executed"

            # System control
            elif action == 'system':
                if len(parts) < 2:
                    return "Please specify a system action"
                
                sys_cmd = parts[1]
                if sys_cmd == 'lock':
                    subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True)
                elif sys_cmd == 'shutdown':
                    subprocess.run('shutdown /s /t 60', shell=True)
                elif sys_cmd == 'restart':
                    subprocess.run('shutdown /r /t 60', shell=True)
                elif sys_cmd == 'cancel':
                    subprocess.run('shutdown /a', shell=True)
                return f"System {sys_cmd} command executed"

            # Screenshot
            elif action == 'screenshot':
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                if len(parts) > 1 and parts[1] == 'region':
                    # Region screenshot
                    print("Select region to capture...")
                    screenshot = ImageGrab.grab()  # Need to implement region selection
                else:
                    # Full screen
                    screenshot = ImageGrab.grab()
                filename = f"screenshot_{timestamp}.png"
                screenshot.save(filename)
                return f"Screenshot saved as {filename}"

            # Clipboard operations
            elif action == 'clipboard':
                if len(parts) > 1:
                    if parts[1] == 'copy':
                        pyautogui.hotkey('ctrl', 'c')
                        return "Copied selection to clipboard"
                    elif parts[1] == 'paste':
                        pyautogui.hotkey('ctrl', 'v')
                        return "Pasted from clipboard"

            # Default command execution
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr
            
        except Exception as e:
            return str(e)

def create_embeddings(embeddings_path: str = config["embeddings_path"]) -> HuggingFaceInstructEmbeddings:
    """Create embeddings instance for vector storage."""
    return HuggingFaceInstructEmbeddings(model_name=embeddings_path)

def create_chat_memory(chat_history: List) -> ConversationBufferWindowMemory:
    """Create conversation memory with specified history."""
    return ConversationBufferWindowMemory(memory_key="history", chat_memory=chat_history, k=3)

def load_vectordb(embeddings: HuggingFaceInstructEmbeddings) -> Chroma:
    """Load or create vector database for document storage."""
    persistent_client = chromadb.PersistentClient("chroma_db")
    return Chroma(
        client=persistent_client,
        collection_name="pdfs",
        embedding_function=embeddings
    )

class GroqChatChain:
    """
    Main chat chain implementation using Groq LLM.
    """
    
    def __init__(self, chat_history: List, model_name: str = "llama-3.1-70b-versatile"):
        """
        Initialize chat chain with conversation history.
        
        Args:
            chat_history: List of previous conversation messages
            model_name: Name of the model to use
        """
        self.memory = create_chat_memory(chat_history)
        self.llm = GroqLLM(model_name=model_name)
    
    def run(self, user_input: str) -> str:
        """
        Process user input and return final response.
        
        Args:
            user_input: User's query or prompt
            
        Returns:
            String containing the final response
        """
        final_response = None
        for title, content, _ in self.run_with_steps(user_input):
            if "Final Answer" in title:
                final_response = content
        return final_response
    
    def run_with_steps(
        self,
        user_input: str
    ) -> Generator[Tuple[str, str, float], None, None]:
        """
        Process user input with visible reasoning steps.
        
        Args:
            user_input: User's query or prompt
            
        Yields:
            Tuples of (step_title, step_content, thinking_time)
        """
        yield from self.llm.generate_response_with_steps(
            user_input,
            history=self.memory.chat_memory.messages
        )

class GroqPDFChatChain:
    """
    Specialized chat chain for handling PDF document queries.
    """
    
    def __init__(self, chat_history: List, model_name: str = "llama-3.1-70b-versatile"):
        """
        Initialize PDF chat chain with conversation history.
        
        Args:
            chat_history: List of previous conversation messages
            model_name: Name of the model to use
        """
        self.memory = create_chat_memory(chat_history)
        self.llm = GroqLLM(model_name=model_name)
        self.vector_db = load_vectordb(create_embeddings())
    
    def run(self, user_input: str) -> str:
        """
        Process user input with PDF context and return final response.
        
        Args:
            user_input: User's query about PDF content
            
        Returns:
            String containing the final response
        """
        final_response = None
        for title, content, _ in self.run_with_steps(user_input):
            if "Final Answer" in title:
                final_response = content
        return final_response
    
    def run_with_steps(
        self,
        user_input: str
    ) -> Generator[Tuple[str, str, float], None, None]:
        """
        Process PDF-related query with visible reasoning steps.
        
        Args:
            user_input: User's query about PDF content
            
        Yields:
            Tuples of (step_title, step_content, thinking_time)
        """
        # Retrieve relevant documents
        docs = self.vector_db.similarity_search(user_input, k=3)
        doc_context = "\n\n".join(
            f"Document {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(docs)
        )
        
        enhanced_prompt = f"""Context from relevant documents:
        {doc_context}
        
        User question: {user_input}
        
        Please analyze the documents and provide a detailed response."""
        
        yield from self.llm.generate_response_with_steps(
            enhanced_prompt,
            history=self.memory.chat_memory.messages
        )

def load_normal_chain(chat_history: List, model_name: str = "llama-3.1-70b-versatile") -> GroqChatChain:
    """Create and return a standard chat chain."""
    return GroqChatChain(chat_history, model_name=model_name)

def load_pdf_chat_chain(chat_history: List, model_name: str = "llama-3.1-70b-versatile") -> GroqPDFChatChain:
    """Create and return a PDF-specialized chat chain."""
    return GroqPDFChatChain(chat_history, model_name=model_name)