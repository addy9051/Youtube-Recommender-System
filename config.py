import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "300"))
    MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", "8"))