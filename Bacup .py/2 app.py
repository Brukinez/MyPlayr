from supabase import create_client

URL_SUPABASE = "https://zxgsbcswuchrwmdcmntg.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4Z"

# Creiamo una connessione al database Supabase che useremo sempre
supabase = create_client(URL_SUPABASE, KEY_SUPABASE)
