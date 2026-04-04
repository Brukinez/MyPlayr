import os
from supabase import create_client
import streamlit as st
from dotenv import load_dotenv

# Carichiamo il .env subito per sicurezza
load_dotenv()

def get_supabase_client():
    url = None
    key = None

    # 1. Prova prima da Streamlit Secrets (Cloud)
    try:
        if "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass # Non siamo in Streamlit o Secrets non è configurato

    # 2. Se non trovate, prova da Variabili d'Ambiente (.env locale)
    if not url or not key:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    # 3. Controllo di sicurezza
    if not url or not key:
        raise ValueError("ERRORE: SUPABASE_URL o SUPABASE_KEY non trovate! Controlla .env o Secrets.")

    # 4. PULIZIA E CREAZIONE (Fondamentale per evitare il 401)
    # .strip() rimuove spazi e caratteri invisibili
    return create_client(url.strip(), key.strip())

# Istanza singola
supabase = get_supabase_client()
