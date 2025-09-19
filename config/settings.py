import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    PAKRAIL_URL = "https://pakrail.gov.pk/"
    
    # Selenium Configuration
    SELENIUM_TIMEOUT = 30
    IMPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 30
    
    # AI Agent Configuration
    AI_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
    MAX_RETRIES = 3
    
    # Scraper Configuration
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]