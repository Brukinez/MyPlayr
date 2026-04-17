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
EMERGENT_CSS = """
<style>
    /* 1. LO SFONDO */
    .stApp {
        background-color: #252b32 !important; 
    }

    /* 2. FORZA IL VERDE SUGLI ACCENTI (SOVRASCRIVE IL SECONDARY) */
    div.stButton > button {
        transition: 0.3s ease !important;
    }

    /* COLPIAMO I TUOI DUE BOTTONI SPECIFICI */
    button[key="home_login_btn"], 
    button[key="home_reg_btn"] {
        background-color: rgb(41, 168, 71) !important;
        color: white !important;
        border: none !important;
        font-weight: 800 !important;
        height: 54px !important;
    }

    /* EFFETTO AL PASSAGGIO DEL MOUSE */
    button[key="home_login_btn"]:hover, 
    button[key="home_reg_btn"]:hover {
        background-color: #24e170 !important;
        color: white !important;
        box-shadow: 0 5px 15px rgba(41, 168, 71, 0.4) !important;
    }


          /* --- STILE DELLE SCHEDE (CARD) - AGGIORNATO DALLO SCREENSHOT --- */
    .mcp-card {
        background-color: #38404a !important; /* Il grigio esatto della tua foto */
        border: 1px solid rgba(255, 255, 255, 0.05); /* Bordino sottile e discreto */
        border-radius: 12px;               /* Angoli arrotondati perfetti */
        padding: 20px;                     /* Spazio interno */
        color: white;
        font-family: 'Inter', sans-serif;
        margin-bottom: 30px;
        transition: 0.3s ease;             /* Movimento fluido */
        height: 100%;                      /* Altezza uguale per tutte */
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); /* Ombra per l'effetto 3D */
    }

    .mcp-card:hover {
        transform: translateY(-5px);       /* La scheda si alza leggermente */
        border-color: rgb(41, 168, 71);    /* Il bordo diventa del tuo verde */
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5); /* L'ombra aumenta al passaggio del mouse */
    }

        /* RENDE I TITOLI DELLE CARD IN GRASSETTO */
    .mcp-card h3, 
    .mcp-card b,
    .mcp-card strong {
        font-weight: 800 !important;      /* Grassetto molto marcato */
        font-size: 24px !important;       /* Dimensione equilibrata */
        color: white !important;
        text-transform: uppercase !important; /* Forza il maiuscolo */
        letter-spacing: 1px !important;   /* Un po' di spazio tra le lettere per eleganza */
        display: block !important;
        margin-bottom: 15px !important;   /* Spazio tra titolo e descrizione */
    }

    
    /* ISTRUZIONE PER IL TESTO (18PX) */
    .mcp-card p {
        font-size: 16px !important;
        color: #94a3b8;                    /* Grigio chiaro leggibile */
        line-height: 1.6;
        margin-top: 10px;
    }

        /* --- SCATOLA DELL'ICONA NELLE SCHEDE (CARD) --- */
    .icon-box {
        width: 56px;
        height: 56px;
        background-color: rgba(41, 168, 71, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        transition: background-color 0.3s;
    }

    /* --- RIPRISTINO BADGE VERDE (LA RIVOLUZIONE...) --- */
    .hero-badge {
        display: inline-flex !important;
        align-items: center !important;
        background-color: rgba(41, 168, 71, 0.2) !important; /* Verde trasparente */
        border: 0.88px solid rgba(41, 168, 71, 0.3) !important;
        border-radius: 9999px !important;
        color: rgb(41, 168, 71) !important; /* Testo verde */
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 22px !important;
        padding: 8px 16px !important;
        margin-bottom: 32px !important;
        text-align: center !important;
    }

      
    /* --- SEZIONE STATISTICHE (STRISCIA) --- */
    .stats-container {
        background-color: #38404a; /* Lo stesso grigio delle tue card */
        padding: 25px 5%;
        display: flex;
        justify-content: space-around;
        align-items: center;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        margin: 50px 0;
    }

    .stat-item {
        text-align: center;
    }

    .stat-number {
        color: rgb(41, 168, 71); /* Il tuo verde */
        font-size: 35px;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }

    .stat-label {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
        /* --- L'UNICA GRANDE SCATOLA DELLA NEWSLETTER --- */
    div[data-testid="stForm"] {
        background-color: #38404a !important; /* Il grigio delle tue card */
        max-width: 800px !important;         /* Larghezza massima della scatola */
        margin: 50px auto !important;        /* LA CENTRA NEL SITO */
        padding: 50px !important;            /* Spazio interno per far respirare i testi */
        border-radius: 20px !important;
            /* Bordino verde sottile attorno alla card */
    border: 1px solid rgba(41, 168, 71, 0.8) !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5) !important;
        text-align: center !important;
    }
 
    /* SISTEMIAMO L'INPUT E IL BOTTONE SULLA STESSA RIGA */
    div[data-testid="stForm"] .stHorizontalBlock {
        align-items: flex-end !important; /* Allinea perfettamente il tasto all'input */
        gap: 15px !important;
    }

    /* L'INPUT EMAIL */
    div[data-testid="stForm"] input {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        height: 60px !important;
        border-radius: 8px !important;
    }

    /* IL TASTO ISCRIVITI */
    div[data-testid="stForm"] button {
        background-color: rgb(41, 168, 71) !important;
        color: white !important;
        height: 25px !important;
        width: 100% !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        text-transform: uppercase !important;
        border: none !important;
    }


    /* --- SEZIONE FINALE PRONTO A DIVENTARE UN CAMPIONE --- */
    .cta-final-section {
        background-color: #212b27; /* Verde scurissimo quasi nero */
        padding: 100px 5%;
        text-align: center;
        border-top: 1px solid rgba(41, 168, 71, 0.2);
        margin-top: 50px;
    }

    .cta-final-section h2 {
        color: white !important;
        font-size: 45px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
        margin-bottom: 20px !important;
        text-transform: uppercase;
    }

    .cta-final-section .highlight-green {
        color: rgb(41, 168, 71) !important;
    }
   
 /* Nasconde la barra grigia originale di Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Spazio per evitare che il contenuto finisca sotto la barra fissa */
    .main .block-container {
        padding-top: 100px !important;
    }

            /* BARRA FISSA (STICKY) - COLORE CHIARO E POSIZIONE ORIZZONTALE */
    .sticky-navbar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 20px;
       background-color: #38404a !important; /* Lo stesso scuro delle card */
        backdrop-filter: blur(10px);
        display: flex !important;           /* Mette logo e spazio in riga */
        align-items: center !important;     /* Centra tutto verticalmente */
        justify-content: space-between !important;
        padding: 0 5%;
        z-index: 999999;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

        /* QUESTO SERVE A METTERE MC E MYCLIPZO UNO DI FIANCO ALL'ALTRO */
    .logo-container {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 12px !important;
    }

    .mc-box {
        background-color: rgb(41, 168, 71); 
        color: white;
        font-weight: 900;
        padding: 12px 12px;
        border-radius: 4px;
        font-size: 30px;
        line-height: 1;
    }

    .brand-name {
        color: white; 
        font-size: 30px;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
    }
               
        /* RIDUCIAMO IL RIQUADRO E INGRANDIAMO IL TESTO */
    .stApp div.stButton > button[kind="primary"] {
        background-color: rgb(41, 168, 71) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        
        /* 1. GRANDEZZA SCRITTA: Cambia 22px per ingrandire/rimpicciolire */
        font-size: 22px !important; 
        font-weight: 800 !important;
        
        /* 2. ALTEZZA RIQUADRO: Riduciamo il padding (sopra e sotto) */
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        min-height: 10px !important; /* Toglie l'altezza minima di Streamlit */
        height: auto !important;     /* Si adatta al testo */
        
        width: auto !important;      /* Lo rende largo quanto serve al testo */
        display: block !important;
        margin: 0 auto !important;   /* Lo centra */
    }
     /* ELIMINA IL BUG ROSSO SENZA CAMBIARE LE DIMENSIONI */
    .stApp div.stButton > button[kind="primary"]:focus,
    .stApp div.stButton > button[kind="primary"]:active {
        background-color: rgb(41, 168, 71) !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* --- BLINDATURA TOTALE ANTI-ROSSO --- */
    /* 1. Blocca i bottoni verdi (Primary) in ogni istante del click */
    div.stButton > button[kind="primary"], 
    div.stButton > button[kind="primary"]:hover, 
    div.stButton > button[kind="primary"]:focus, 
    div.stButton > button[kind="primary"]:active {
        background-color: rgb(41, 168, 71) !important;
        color: white !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        transition: none !important; /* Toglie il flash del tema originale */
    }

    /* ATTACCO FINALE AI RIQUADRI NERI */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
    }
    
    /* Questo elimina il rettangolo nero che appare quando il mouse è sopra o quando clicchi */
    .stButton > button[kind="secondary"]:hover, 
    .stButton > button[kind="secondary"]:active, 
    .stButton > button[kind="secondary"]:focus {
        background: transparent !important;
        color: white !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 2. Regoliamo la scritta (Aumenta i 22px se la vuoi più grande) */
    button[key^="f_"] p {
        font-size: 22px !important; 
        color: #94a3b8 !important; /* Grigio MyPlayr */
        text-align: left !important;
        margin: 0 !important;
        background: transparent !important;
    }

    /* 3. Effetto Hover: la scritta si illumina senza far apparire grigio */
    button[key^="f_"]:hover p {
        color: white !important;
    }

    /* Assicuriamoci che rimanga trasparente anche quando ci clicchi o lo selezioni */
    button[key^="f_"]:hover, 
    button[key^="f_"]:active, 
    button[key^="f_"]:focus {
        background-color: transparent !important;
        background: transparent !important;
        color: white !important; /* La scritta diventa bianca */
    }

    /* 3. Sistema il riquadro della password sviluppatore */
    .stTextInput div[data-baseweb="input"] {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: rgb(41, 168, 71) !important;
    }

    /* TRASFORMA I BOTTONI IN TESTO PURO (STILE MYPLAYR) */
    button[key^="f_"] {
        background: none !important;           /* Rimuove il riquadro nero */
        background-color: transparent !important;
        border: none !important;                /* Rimuove i bordi */
        box-shadow: none !important;            /* Rimuove l'ombra del tasto */
        color: #94a3b8 !important;              /* Grigio azzurrino originale */
        padding: 0 !important;                  /* Attacca la zona cliccabile al testo */
        margin: 0 !important;
        height: auto !important;
        min-height: 0px !important;
        font-size: 20px !important;             /* Puoi cambiarlo manualmente qui */
        font-weight: 500 !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }

    /* Effetto quando passi il mouse: la scritta si illumina senza far apparire riquadri */
    button[key^="f_"]:hover {
        color: white !important;
        background: none !important;
        background-color: transparent !important;
    }


    /* --- OTTIMIZZAZIONE PER SMARTPHONE E TABLET --- */
    @media (max-width: 768px) {
        
        /* 1. IL TITOLO GIGANTE (Hero) */
        /* Lo portiamo da 100px a 45px, altrimenti esce dallo schermo */
        .stApp h1 {
            font-size: 45px !important;
            line-height: 1.1 !important;
        }

        /* 2. LE DESCRIZIONI (Sotto il titolo e nelle card) */
        .stApp p {
            font-size: 16px !important;
            line-height: 1.4 !important;
        }

        /* 3. LE CARD (Più compatte) */
        .mcp-card {
            padding: 15px !important;
            margin-bottom: 15px !important;
        }
        
        .mcp-card p {
            font-size: 16px !important; /* Riduciamo i 24px del PC a 16px */
        }

        /* 4. I BOTTONI VERDI (Meno ingombranti) */
        button[key="home_login_btn"], 
        button[key="home_reg_btn"] {
            font-size: 18px !important;
            padding: 10px 20px !important;
            width: 100% !important; /* Su mobile è meglio averli a tutta larghezza */
        }

        /* 5. IL FOOTER (Scritte leggibili ma non giganti) */
        button[key^="f_"] {
            font-size: 16px !important;
        }
        
        .footer-title {
            font-size: 14px !important;
            margin-top: 20px !important;
        }

        /* 6. NEWSLETTER (La card si adatta) */
        div[data-testid="stForm"] {
            padding: 20px !important;
            margin: 10px !important;
        }
    }

            /* 7. NAVBAR MOBILE (PIÙ SOTTILE) */
        .sticky-navbar {
            height: 65px !important; /* Ridotta da 84px a 65px */
            padding: 0 15px !important;
        }

        .mc-box {
            font-size: 20px !important; /* Logo MC più piccolo */
            padding: 6px 10px !important;
        }

        .brand-name {
            font-size: 20px !important; /* Nome MyClipzo più piccolo */
        }

        /* Spazio in alto per il contenuto (per non finire sotto la navbar ridotta) */
        .main .block-container {
            padding-top: 85px !important; 
        }

            /* 8. STATISTICHE SU SMARTPHONE (In colonna) */
    @media (max-width: 768px) {
        .stats-container {
            flex-direction: column !important; /* Solo qui diventano verticali */
            gap: 40px !important;
            padding: 50px 10px !important;
            text-align: center !important;
        }

        .stat-item {
            width: 100% !important;
        }

        .stat-number {
            font-size: 42px !important; /* Numeri leggibili su mobile */
        }
    }

    /* ATTACCO FINALE AI RIQUADRI NERI */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
    }
    
    /* Questo elimina il rettangolo nero che appare quando il mouse è sopra o quando clicchi */
    .stButton > button[kind="secondary"]:hover, 
    .stButton > button[kind="secondary"]:active, 
    .stButton > button[kind="secondary"]:focus {
        background: transparent !important;
        color: white !important;
        border: none !important;
        box-shadow: none !important;
    }

    .stat-card {
    background: rgba(255,255,255,0.03);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
}

.stat-card h1 {
    color: white;
    margin: 5px 0;
}

.stat-card p {
    color: #94a3b8;
    margin: 0;
}

.stat-card {
    background: rgba(255,255,255,0.03);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
}

.stat-card h1 {
    color: white;
    margin: 5px 0;
}

.stat-card p {
    color: #94a3b8;
    margin: 0;
}
</style>
"""

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
