import streamlit as st
import os
import re
from supabase import create_client
from dotenv import load_dotenv

# 1. Carica variabili dal file .env (Locale)
load_dotenv()

# BLOCCO 2 --- CONNESSIONE MANCANTE RIPRISTINATA ---
URL_SUPABASE = "https://zxgsbcswuchrwmdcmntg.supabase.co"
# Incolla qui la Service Role Key tra le virgolette
KEY_SUPABASE = st.secrets["SUPABASE_KEY"]

if 'supabase' not in st.session_state:
    st.session_state.supabase = create_client(URL_SUPABASE, KEY_SUPABASE)
supabase = st.session_state.supabase

def make_direct_link(url):
    """
    Per link Google Drive: ricava l'id del file e restituisce un URL in formato
    uc?export=download&id=... (adatto al player). Altrimenti restituisce l'URL originale.
    Valori mancanti (None, vuoti, NaN) -> None (così non si passa nulla a st.video).
    """
    if url is None:
        return None
    try:
        if pd.isna(url):
            return None
    except (TypeError, ValueError):
        pass
    s = str(url).strip()
    if not s or s.lower() in ("none", "nan", "null"):
        return None
    if "drive.google.com" not in s:
        return s
    parsed = urlparse(s)
    qs = parse_qs(parsed.query)
    file_id = (qs.get("id") or [None])[0]
    if file_id:
        file_id = file_id.strip()
    if not file_id:
        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", s)
        if m:
            file_id = m.group(1)
    if not file_id:
        return s
    return f"https://drive.google.com/uc?export=download&id={file_id}"
URL_SUPABASE = "https://supabase.co"
KEY_SUPABASE = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not URL_SUPABASE or not KEY_SUPABASE:
    st.error("⚠️ Credenziali Supabase mancanti!")

supabase = create_client(URL_SUPABASE, KEY_SUPABASE)

# BLOCCO 6 --- 2. GESTIONE PERCORSI (FOLDERS) ---
# Usiamo questo metodo per far funzionare il codice su ogni PC (casa o centro sportivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cartelle principali
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")
CLIP_DIR = os.path.join(BASE_DIR, "CLIP_TAGLIATE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"
# Creazione automatica cartelle mancanti
for cartella in [VIDEO_DIR, IMG_DIR, CLIP_DIR]:
    if not os.path.exists(cartella):
        os.makedirs(cartella)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")
CLIP_DIR = os.path.join(BASE_DIR, "CLIP_TAGLIATE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"

# BLOCCO 8 --- : CONNESSIONE CLOUD E LOGICA CLIP ---

# Importiamo la connessione dal tuo file database.py
from database import supabase 

# Configurazione Percorsi per le Clip (Google Drive o Locale)
# NOTA: Se il disco G: non è collegato, il programma userà una cartella locale di emergenza
# Prova a usare il Google Drive, altrimenti usa una cartella locale sicura
CLIP_GDRIVE = r"G:\Il mio Drive\CLIP_MYPLAYR"

if not os.path.exists(CLIP_GDRIVE):
    # Se il disco G non esiste (es. sei sul Web), usa la cartella CLIP_TAGLIATE che abbiamo creato nel Blocco 2
    CLIP_GDRIVE = CLIP_DIR

# BLOCCO 7 --- STILE GLOBALE (EMERGENT STYLE) ---
# Definiamo il CSS in cima al file, poi lo applichiamo subito dopo set_page_config.
EMERGENT_CSS = """<style>stApp { background-color: red !important; }</style>"""

# --- 2. HTML DELLA NAVBAR (LOGO E NOME) ---
st.markdown("""
    <div class='sticky-navbar'>
        <div class='logo-container'>
            <div class='mc-box'>MC</div>
            <div class='brand-name'>MyClipzo</div>
        </div>
        <div></div> <!-- Spazio vuoto per bilanciare il flex -->
    </div>
""", unsafe_allow_html=True)
EMERGENT_CSS = """
<style>
    /* Incolla qui il tuo CSS completo */
</style>
"""

def apply_style():
    st.markdown(EMERGENT_CSS, unsafe_allow_html=True)
