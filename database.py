import os
from supabase import create_client
import streamlit as st

# Per caricare variabili d'ambiente in locale
from dotenv import load_dotenv

def get_supabase_client():
    """
    Crea il client Supabase leggendo le chiavi:
    - da st.secrets se in ambiente Streamlit Cloud
    - da variabili d'ambiente (.env) se in locale
    """

    if st.secrets and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    else:
        load_dotenv()  # carica .env in locale
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    return create_client(url, key)


# Crea una singola istanza da importare negli altri file
supabase = get_supabase_client()
