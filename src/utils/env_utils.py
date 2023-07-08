"""
Helper functions for retrieving keys from environment variables.

Written by Aaron Ward
"""

import os
from dotenv import load_dotenv, dotenv_values

def get_openai_key(env_path):
    """
    Retrieves the OpenAI API key from the environment.

    Args:
        env_path (str): Path to the .env file.
    Returns:
        str: OpenAI API key.
    Raises:
        ValueError: If the OPENAI_API_KEY is not set in the .env file or the environment.
    """

    load_dotenv(dotenv_path=env_path, verbose=True)

    # Set the OPENAI_API_KEY environment variable
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is not set in the .env file or the environment")

    return openai_api_key