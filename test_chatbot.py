from gemini_client import GeminiChat

def test_chat():
    try:
        # Initialize the chat client
        chat_client = GeminiChat()
        
        # Test a simple message
        message = "Hello! What can you tell me about CatanduanesConnect?"
        print(f"\nUser: {message}")
        response = chat_client.send_message(message)
        print(f"Assistant: {response}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_chat()