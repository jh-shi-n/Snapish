from contextlib import contextmanager
import openai
import os
from functools import lru_cache

class OpenAIClientManager:
    _instance = None
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_client(cls):
        if not cls._instance:
            cls._instance = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        return cls._instance
    
    @classmethod
    def clear_client(cls):
        cls._instance = None
        cls.get_client.cache_clear()

@contextmanager
def openai_client():
    try:
        client = OpenAIClientManager.get_client()
        yield client
    finally:
        pass  # Client will be cached for reuse