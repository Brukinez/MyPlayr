import streamlit as st
import os
import re
from supabase import create_client
from dotenv import load_dotenv

# 1. Carica variabili dal file .env (Locale)
load_dotenv()

# 2. Connessione Supabase (Blocco 2)
URL_SUPABASE = "https://supabase.co"
KEY_SUPABASE = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not URL_SUPABASE or not KEY_SUPABASE:
    st.error("⚠️ Credenziali Supabase mancanti!")

supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

# 3. Gestione Percorsi (Blocco 6 e 8)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")
CLIP_DIR = os.path.join(BASE_DIR, "CLIP_TAGLIATE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"

# 4. Stile Grafico (Blocco 7)
# INCOLLA QUI TUTTO IL TUO LUNGO EMERGENT_CSS TRA LE TRIPLE VIRGOLETTE
EMERGENT_CSS = """
<style>
    /* Incolla qui il tuo CSS completo */
</style>
"""

def apply_style():
    st.markdown(EMERGENT_CSS, unsafe_allow_html=True)
