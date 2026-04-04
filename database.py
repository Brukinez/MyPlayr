import os
from dotenv import load_dotenv
from supabase import create_client

# Forza la ricerca del file .env nella cartella corrente
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Controllo di sicurezza: se sono vuoti, il programma te lo dice subito
if not url or not key:
    print("❌ ERRORE: Chiavi non trovate nel file .env!")
else:
    print("✅ Chiavi caricate correttamente.")

supabase = create_client(url, key)
