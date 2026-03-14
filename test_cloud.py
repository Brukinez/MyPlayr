from supabase import create_client

# INCOLLA QUI I TUOI DATI REALI TRA LE VIRGOLETTE
URL = "https://zxgsbcswuchrwmdcmntg.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4Z3NiY3N3dWNocndtZGNtbnRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0NjI2ODUsImV4cCI6MjA4OTAzODY4NX0.-SM7y6iXg8H14njnu3QYNtop5pezZsGODC0F_zOY_v4"

try:
    supabase = create_client(URL, KEY)
    
    # Proviamo a scrivere un match di test
    test_data = {"data": "14-03-2026", "ora": "12:00", "campo": "Test Supabase", "stato": "PROGRAMMATO"}
    supabase.table("calendario").insert(test_data).execute()
    
    print("✅ VITTORIA TOTALE! Il PC ha scritto nel Cloud.")
    print("Controlla su Supabase nella tabella 'calendario': vedrai la riga!")
except Exception as e:
    print(f"❌ ANCORA ERRORE: {e}")
