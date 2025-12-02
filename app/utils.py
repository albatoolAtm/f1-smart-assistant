from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file

def get_api_key():
    """
    Returns the OpenAI API key from the environment.
    """
    api_key = os.getenv("OPENAI_API_KEY")  # Read the OpenAI key
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")

    return api_key
