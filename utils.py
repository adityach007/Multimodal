import json
import datetime

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