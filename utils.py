import json
import datetime
import pandas as pd
from docx import Document

def get_timestamp():
    """Generate a timestamp string for new chat sessions."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def save_chat_history_json(history, filepath):
    """Save chat history to a JSON file."""
    history_data = []
    for message in history:
        history_data.append({
            "type": message.type,
            "content": message.content
        })
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

def load_chat_history_json(filepath):
    """Load chat history from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        history = []
        for message in history_data:
            history.append(type('Message', (), {
                'type': message['type'],
                'content': message['content']
            }))
        return history
    except FileNotFoundError:
        return []

def get_file_extension(filename):
    """Get file extension from filename."""
    return filename.rsplit('.', 1)[-1].lower()

def generate_file_preview(file_obj, file_type):
    """Generate a preview of file content based on file type."""
    try:
        if file_type == 'txt':
            content = file_obj.read().decode('utf-8')
            return content[:1000] + '...' if len(content) > 1000 else content
            
        elif file_type == 'csv':
            df = pd.read_csv(file_obj)
            return df.head().to_html()
            
        elif file_type == 'xlsx' or file_type == 'xls':
            df = pd.read_excel(file_obj)
            return df.head().to_html()
            
        elif file_type == 'docx':
            doc = Document(file_obj)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return content[:1000] + '...' if len(content) > 1000 else content
            
        elif file_type in ['png', 'jpg', 'jpeg']:
            return "Image preview available"
            
        elif file_type == 'pdf':
            return "PDF preview available"
            
        else:
            return "Preview not available for this file type"
            
    except Exception as e:
        return f"Error generating preview: {str(e)}"