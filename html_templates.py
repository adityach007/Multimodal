# html_templates.py
css = '''
<style>
:root {
    --primary-bg: #1a1c24;
    --message-user-bg: #2b313e;
    --message-bot-bg: #3a4152;
    --accent-color: #4CAF50;
    --text-color: #ffffff;
    --text-secondary: #a0aec0;
}

body {
    background-color: var(--primary-bg);
    font-family: 'Inter', sans-serif;
}

.chat-message {
    padding: 1.5rem;
    border-radius: 1rem;
    margin-bottom: 1.5rem;
    display: flex;
    animation: fadeIn 0.5s ease-out;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease;
}

.chat-message:hover {
    transform: translateY(-2px);
}

.chat-message.user {
    background-color: var(--message-user-bg);
}

.chat-message.bot {
    background-color: var(--message-bot-bg);
}

.chat-message .avatar {
    width: 15%;
    min-width: 60px;
}

.chat-message .avatar img {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--accent-color);
    transition: transform 0.3s ease;
}

.chat-message .avatar img:hover {
    transform: scale(1.1);
}

.chat-message .message {
    width: 85%;
    padding: 0 1.5rem;
    color: var(--text-color);
    line-height: 1.6;
}

.thinking-steps {
    margin-top: 1rem;
    padding: 1rem;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.thinking-steps .step {
    margin-bottom: 1rem;
    padding: 1rem;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    transition: background-color 0.3s ease;
}

.thinking-steps .step:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.view-steps-btn {
    padding: 0.75rem 1.25rem;
    background-color: var(--accent-color);
    border: none;
    border-radius: 0.5rem;
    color: white;
    cursor: pointer;
    margin-top: 1rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.view-steps-btn:hover {
    background-color: #45a049;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.timestamp {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.75rem;
    font-style: italic;
}

.scroll-top-btn {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background-color: var(--accent-color);
    color: white;
    border: none;
    border-radius: 50%;
    width: 3.5rem;
    height: 3.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    transition: all 0.3s ease;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    opacity: 0;
    transform: translateY(100px);
}

.scroll-top-btn.visible {
    opacity: 1;
    transform: translateY(0);
}

.scroll-top-btn:hover {
    background-color: #45a049;
    transform: translateY(-2px);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Loading indicator for bot responses */
.typing-indicator {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    margin-top: 0.5rem;
}

.typing-indicator span {
    width: 0.5rem;
    height: 0.5rem;
    background: var(--accent-color);
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
</style>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
'''

def get_bot_template(ai_content, timestamp=None, thinking_steps=None):
    steps_button = ""
    steps_content = ""
    if thinking_steps:
        steps_button = '<button onclick="toggleSteps(this)" class="view-steps-btn">View Thinking Process</button>'
        steps_content = '<div class="thinking-steps" style="display: none;">'
        for step in thinking_steps:
            steps_content += f'<div class="step"><strong>{step[0]}</strong><br>{step[1]}</div>'
        steps_content += '</div>'
    
    timestamp_html = f'<div class="timestamp">{timestamp}</div>' if timestamp else ''
    
    return f'''
    <div class="chat-message bot">
        <div class="avatar">
            <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png">
        </div>
        <div class="message">
            {ai_content}
            {timestamp_html}
            {steps_button}
            {steps_content}
            <div class="typing-indicator" style="display: none;">
                <span></span><span></span><span></span>
            </div>
        </div>
    </div>
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

# Add JavaScript for enhanced functionality
js = '''
<script>
// Scroll to top button functionality
window.onscroll = function() {
    const scrollBtn = document.querySelector('.scroll-top-btn');
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        scrollBtn.classList.add('visible');
    } else {
        scrollBtn.classList.remove('visible');
    }
};

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function toggleSteps(button) {
    const stepsDiv = button.nextElementSibling;
    const isHidden = stepsDiv.style.display === 'none';
    
    if (isHidden) {
        stepsDiv.style.display = 'block';
        button.textContent = 'Hide Thinking Process';
        stepsDiv.style.animation = 'fadeIn 0.5s ease-out';
    } else {
        stepsDiv.style.display = 'none';
        button.textContent = 'View Thinking Process';
    }
}

// Add smooth scrolling to new messages
function scrollToBottom(smooth = true) {
    window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

// Show/hide typing indicator
function toggleTyping(show) {
    const indicators = document.querySelectorAll('.typing-indicator');
    const lastIndicator = indicators[indicators.length - 1];
    if (lastIndicator) {
        lastIndicator.style.display = show ? 'flex' : 'none';
    }
}
</script>

<div class="scroll-top-btn" onclick="scrollToTop()">↑</div>
'''
