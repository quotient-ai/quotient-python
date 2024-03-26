import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
load_dotenv(dotenv_path)

if not os.getenv("SUPABASE_URL"):
    raise ValueError("SUPABASE_URL not found in .env.test")