# html_templates.py
css = '''
<style>
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
}
.chat-message.user {
    background-color: #2b313e;
}
.chat-message.bot {
    background-color: #475063;
}
.chat-message .avatar {
    width: 20%;
}
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
}
.chat-message .message {
    width: 80%;
    padding: 0 1.5rem;
    color: #fff;
}
.thinking-steps {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #1e2635;
    border-radius: 0.5rem;
}
.thinking-steps .step {
    margin-bottom: 1rem;
    padding: 1rem;
    background-color: #2b313e;
    border-radius: 0.5rem;
}
.view-steps-btn {
    padding: 0.5rem 1rem;
    background-color: #4CAF50;
    border: none;
    border-radius: 0.25rem;
    color: white;
    cursor: pointer;
    margin-top: 0.5rem;
}
.view-steps-btn:hover {
    background-color: #45a049;
}
.timestamp {
    font-size: 0.8rem;
    color: #a0aec0;
    margin-top: 0.5rem;
}
.scroll-top-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
</style>
'''

def get_bot_template(ai_content, timestamp=None, thinking_steps=None):
    steps_button = ""
    steps_content = ""
    if thinking_steps:
        steps_button = '<button onclick="toggleSteps(this)" class="view-steps-btn">View Thinking Steps</button>'
        steps_content = '<div class="thinking-steps" style="display: none;">'
        for step in thinking_steps:
            steps_content += f'<div class="step"><strong>{step[0]}</strong><br>{step[1]}</div>'
        steps_content += '</div>'
    
    timestamp_html = f'<div class="timestamp">{timestamp}</div>' if timestamp else ''
    
    return f'''
    <div class="chat-message bot">
        <div class="avatar">
            <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
        </div>
        <div class="message">
            {ai_content}
            {timestamp_html}
            {steps_button}
            {steps_content}
        </div>
    </div>
    <script>
    function toggleSteps(button) {{
        const stepsDiv = button.nextElementSibling;
        const isHidden = stepsDiv.style.display === 'none';
        stepsDiv.style.display = isHidden ? 'block' : 'none';
        button.textContent = isHidden ? 'Hide Thinking Steps' : 'View Thinking Steps';
    }}
    </script>
    '''

def get_user_template(user_content, timestamp=None):
    timestamp_html = f'<div class="timestamp">{timestamp}</div>' if timestamp else ''
    return f'''
    <div class="chat-message user">
        <div class="avatar">
            <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-5.png">
        </div>
        <div class="message">
            {user_content}
            {timestamp_html}
        </div>
    </div>
    '''