from dotenv import load_dotenv
import os

# Загружаем .env файл
load_dotenv()

# API ключи и прочие настройки
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_SECRET = os.getenv("GEMINI_API_SECRET")
GEMINI_LLM_KEY = os.getenv("GEMINI_LLM_KEY")

# Базовый URL Gemini
GEMINI_API_URL = "https://api.gemini.com/v1"
