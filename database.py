import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# Carica dal file .env (funziona sul tuo PC)
load_dotenv()

# Cerca prima nei Secrets di Streamlit (Online), se non li trova cerca nel .env (Locale)
try:
    URL_SUPABASE = st.secrets["SUPABASE_URL"]
    KEY_SUPABASE = st.secrets["SUPABASE_KEY"]
except:
    URL_SUPABASE = os.getenv("SUPABASE_URL")
    KEY_SUPABASE = os.getenv("SUPABASE_KEY")

# Controllo di sicurezza
if not URL_SUPABASE or not KEY_SUPABASE:
    st.error("Errore: Credenziali Supabase non trovate!")

supabase = create_client(URL_SUPABASE, KEY_SUPABASE)
