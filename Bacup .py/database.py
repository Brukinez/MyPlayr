from supabase import create_client

# Qui devi inserire l'URL del tuo progetto Supabase (già lo hai)
URL_SUPABASE = "https://gsbcswuchrwmdcmntg.supabase.co"

# Qui invece devi la tua "Service Role Key" che trovi nel tuo account Supabase
# Attenzione: questa chiave è segreta, non mostrarla nessuno!
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4Z3NiY3N3dWNocndtZGNtbnRnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzQ2MjY4NSwiZXhwIjoyMDg5MDM4Njg1fQ.SArj3COE9Fy4wrj7fExBl7ACGd3j6UwPEtAuoD-VnIc"

# Questo crea la connessione al database Supabase
supabase = create_client(URL_SUPABASE, KEY_SUPABASE)






