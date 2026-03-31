import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()
URL_SUPABASE = os.getenv("SUPABASE_URL")
KEY_SUPABASE = os.getenv("SUPABASE_KEY")
supabase = create_client(URL_SUPABASE, KEY_SUPABASE)