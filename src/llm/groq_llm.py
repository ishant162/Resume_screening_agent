"""GroqAPI LLM Module"""

from langchain_groq import ChatGroq
from config.settings import settings


class GroqLLM:
    """
    GroqAPI LLM wrapper for interacting with the GroqAPI.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API
        self.model_name = settings.MODEL_NAME

    def get_llm_model(self) -> ChatGroq:
        """
        Get the Groq LLM model based on user input.

        Returns:
            ChatGroq: An instance of the GroqAPI LLM.
        """
        llm = ChatGroq(model=self.model_name, groq_api_key=self.api_key)
        return llm
