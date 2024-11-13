from groq import Groq
import base64
import re

def clean_response(response):
    """
    Clean the response by removing HTML and script tags.
    
    Args:
        response (str): Raw response from the model
    
    Returns:
        str: Cleaned response text
    """
    # Remove HTML tags and script sections
    cleaned = re.sub(r'<[^>]+>', '', response)
    cleaned = re.sub(r'<script>.*?</script>', '', cleaned, flags=re.DOTALL)
    
    # Remove any remaining HTML artifacts
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove timestamps if present (assuming YYYY-MM-DD HH:MM:SS format)
    cleaned = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '', cleaned)
    
    return cleaned

def handle_image(image_bytes, user_message=None, model="llama-3.2-90b-vision-preview"):
    """
    Process an image using Groq's Vision models.
    
    Args:
        image_bytes (bytes): Raw image bytes
        user_message (str, optional): User's query about the image. 
                                      Defaults to a generic description request.
        model (str): Vision model to use
    
    Returns:
        tuple: (success: bool, response: str)
    """
    try:
        # Validate image bytes
        if not image_bytes:
            return False, "No image data provided"

        # If no user message is provided, use a default description request
        if not user_message:
            user_message = "Please describe this image in detail and tell me what you see."
        
        # Encode the image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Initialize Groq client
        client = Groq()
        
        # Create chat completion with image context - removed system message
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model=model,
            max_tokens=1000
        )
        
        # Clean and return the model's response
        raw_response = chat_completion.choices[0].message.content
        return True, clean_response(raw_response)
    
    except Exception as e:
        return False, f"Error processing image: {str(e)}"

def convert_image_to_base64(image_path):
    """
    Convert an image file to a base64 encoded data URL.
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        str: Base64 encoded data URL
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return "data:image/jpeg;base64," + encoded_string