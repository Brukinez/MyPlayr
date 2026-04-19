import streamlit as st
import os
import pandas as pd
import numpy as np
import smtplib
import subprocess # Fondamentale per far lavorare FFmpeg e tagliare i video
from datetime import datetime
from PIL import Image
from email.mime.text import MIMEText
import re
from urllib.parse import urlparse, parse_qs
from supabase import create_client, Client


# --- CONNESSIONE MANCANTE RIPRISTINATA ---
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


# --- BLOCCO STILE GLOBALE (EMERGENT STYLE) ---
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

# --- 1. CONFIGURAZIONE PAGINA ---
# Questo deve essere SEMPRE il primo comando Streamlit del file
st.set_page_config(
    page_title="MyClipzo - Video Analysis Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GESTIONE PERCORSI (FOLDERS) ---
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

# --- BLOCCO 2: STILE E CSS ---
st.markdown(EMERGENT_CSS, unsafe_allow_html=True)


# --- BLOCCO 3: CONNESSIONE CLOUD E LOGICA CLIP ---

# Importiamo la connessione dal tuo file database.py
from database import supabase 

# Configurazione Percorsi per le Clip (Google Drive o Locale)
# NOTA: Se il disco G: non è collegato, il programma userà una cartella locale di emergenza
# Prova a usare il Google Drive, altrimenti usa una cartella locale sicura
CLIP_GDRIVE = r"G:\Il mio Drive\CLIP_MYPLAYR"

if not os.path.exists(CLIP_GDRIVE):
    # Se il disco G non esiste (es. sei sul Web), usa la cartella CLIP_TAGLIATE che abbiamo creato nel Blocco 2
    CLIP_GDRIVE = CLIP_DIR 

# --- FUNZIONE TAGLIO VIDEO (VERSIONE CON UPLOAD E LINK) ---
def taglia_e_registra_clip(video_nome, inizio_sec, durata_sec, utente_email):
    input_p = os.path.join(VIDEO_DIR, video_nome) 
    
    timestamp_clip = datetime.now().strftime('%H%M%S')
    nome_output = f"MyClipzo_{timestamp_clip}.mp4"
    output_p = os.path.join(VIDEO_DIR, nome_output) # Cartella locale temporanea

    comando = [
        'ffmpeg', '-y', '-ss', str(inizio_sec), '-i', input_p, 
        '-t', str(durata_sec), '-c', 'copy', '-movflags', '+faststart', output_p
    ]

    try:
        # 1. Esecuzione Taglio (FFmpeg)
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Upload su Google Drive con Rclone
        print(f"Caricamento clip {nome_output} su Drive...")
        subprocess.run([RCLONE_EXE, "copy", output_p, "remote:CLIP_MYPLAYR/CLIP_UTENTI"], check=True)

        # 3. Otteniamo il link pubblico
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/CLIP_UTENTI/{nome_output}"],
                             capture_output=True, text=True, check=True)
        link_grezzo = res.stdout.strip()
        
        # 4. Pulizia Link (FORMATO CORRETTO PER IL PLAYER)
        video_id = estrai_id_video(link_grezzo) 
        # FIX: Corretto l'URL aggiungendo '://google.com'
        link_embed = f"https://://google.com{video_id}/preview"

        # 5. SINCRONIZZAZIONE TABELLE SUPABASE
        # A. Aggiorniamo la tabella 'comandi_clip' (Quella che vedi nello screenshot)
        # Cambiamo lo stato in COMPLETATO così l'app mostra il video
        supabase.table("comandi_clip").update({
            "url_video": link_embed,
            "stato": "COMPLETATO"
        }).eq("email_utente", utente_email).eq("stato", "RICHIESTO").execute()
        
        # B. Salviamo anche nello storico 'clip_generate' (Come facevi prima)
        supabase.table("clip_generate").insert({
            "email_utente": utente_email,
            "nome_file": nome_output,
            "url_video": link_embed,
            "data_creazione": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }).execute()
        
        # Rimuoviamo il file locale temporaneo
        if os.path.exists(output_p): os.remove(output_p)
        
        print(f"✅ Clip {nome_output} caricata, linkata e sincronizzata su Supabase!")
        return link_embed

    except Exception as e:
        print(f"❌ Errore durante il taglio/upload clip: {e}")
        return None



# --- FUNZIONE NEWSLETTER E CONFERMA EMAIL ---
def invia_conferma_e_salva(email_utente):
    """Salva l'email su Supabase e invia il benvenuto"""
    email_clean = email_utente.strip().lower()

    # 1. SALVATAGGIO CLOUD
    try:
        supabase.table("newsletter").insert({
            "email": email_clean,
            "data_iscrizione": datetime.now().strftime('%Y-%m-%d %H:%M')
        }).execute()
    except Exception as e:
        print(f"Errore database Supabase: {e}")

    # 2. INVIO EMAIL (SMTP GMAIL)
    # Sostituisci le vecchie righe con queste:
    mio_indirizzo = st.secrets["email"]["indirizzo"]
    mia_password = st.secrets["email"]["password"]   
    
    testo_mail = f"Benvenuto in MyClipzo! Da ora potrai rivedere le tue azioni migliori."
    msg = MIMEText(testo_mail)
    msg['Subject'] = "Conferma Iscrizione MyClipzo"
    msg['From'] = mio_indirizzo
    msg['To'] = email_clean

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mio_indirizzo, mia_password)
            server.sendmail(mio_indirizzo, email_clean, msg.as_string())
        return True
    except Exception as e:
        st.warning(f"Newsletter salvata, ma email di conferma non inviata: {e}")
        return False

# --- BLOCCO 5: FUNZIONI UTENTI (SUPABASE CLOUD) ---

def get_utente_per_email(email):
    """Recupera i dati di un utente dal Cloud tramite la sua email"""
    if not email: return None
    
    email_clean = email.strip().lower()
    try:
        # Cerchiamo nella tabella 'utenti' l'email corrispondente
        res = supabase.table("utenti").select("*").eq("email", email_clean).execute()
        
        # Se res.data ha qualcosa, restituiamo il primo (e unico) risultato
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"⚠️ Errore di connessione al database: {e}")
        return None

def crea_nuovo_utente(dati_utente):
    """Registra un nuovo ragazzo o allenatore nel Cloud"""
    try:
        # 1. Pulizia obbligatoria dell'email
        email_pulita = dati_utente["email"].strip().lower()
        dati_utente["email"] = email_pulita
        
        # 2. Controllo: Esiste già questo utente?
        utente_esistente = get_utente_per_email(email_pulita)
        if utente_esistente:
            st.warning("Quest'email è già registrata su MyClipzo!")
            return False
            
        # 3. Se non esiste, procediamo con l'inserimento
        supabase.table("utenti").insert(dati_utente).execute()
        st.success("✅ Registrazione completata con successo!")
        return True
        
    except Exception as e:
        st.error(f"❌ Errore durante la registrazione: {e}")
        return False

# --- BLOCCO: GESTIONE PROFILO UTENTE (SUPABASE) ---

def aggiorna_profilo_social(email, nuovo_tag_ig):
    """
    Aggiorna il tag Instagram dell'utente nel database Cloud.
    Serve per taggare automaticamente i ragazzi nelle clip social.
    """
    try:
        # Pulizia dell'email per sicurezza
        email_clean = email.strip().lower()
        
        # Comando Supabase: Cerca l'utente con quella mail e cambia il campo 'ig_tag'
        supabase.table("utenti").update({"ig_tag": nuovo_tag_ig}).eq("email", email_clean).execute()
        
        st.success(f"✅ Profilo Instagram aggiornato a: {nuovo_tag_ig}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Errore durante l'aggiornamento del profilo: {e}")

def ottieni_dati_profilo(email):
    """
    Recupera tutte le informazioni dell'utente (Bio, Instagram, Foto, Ruolo) 
    dal Cloud per visualizzarle nella pagina Profilo.
    """
    try:
        email_clean = email.strip().lower()
        
        # Interroga Supabase
        res = supabase.table("utenti").select("*").eq("email", email_clean).execute()
        
        # Se trova l'utente, restituisce il primo risultato della lista [0]
        if res.data:
            return res.data[0]
        else:
            return None
    except Exception as e:
        st.error(f"⚠️ Impossibile caricare i dati del profilo: {e}")
        return None

def aggiorna_foto_profilo_db(email, url_foto):
    """
    Funzione aggiuntiva: salva l'indirizzo della foto profilo 
    così l'utente la vede ogni volta che fa il login.
    """
    try:
        email_clean = email.strip().lower()
        supabase.table("utenti").update({"foto_path": url_foto}).eq("email", email_clean).execute()
    except Exception as e:
        print(f"Errore salvataggio URL foto: {e}")

# --- BLOCCO: PROTEZIONE SITO (PASSWORD SVILUPPATORE) ---

# 1. Inizializziamo lo stato della protezione (se non esiste già)
if "password_dev_corretta" not in st.session_state:
    st.session_state["password_dev_corretta"] = False

# 2. Se l'utente non ha ancora inserito la password corretta, fermiamo tutto qui
if not st.session_state["password_dev_corretta"]:
    st.markdown("<h1 style='text-align: center;'>🚧 MyClipzo - Area Protetta</h1>", unsafe_allow_html=True)
    st.info("⚠️ Il sito è in fase di test. Inserisci la password per sbloccare l'anteprima.")
    
    # Creiamo due colonne per un layout pulito
    col_p1, col_p2 = st.columns([2, 1])
    
    with col_p1:
        # Il .strip() rimuove spazi vuoti accidentali prima o dopo la password
        pwd_inserita = st.text_input("Password Sviluppatore", type="password", placeholder="Inserisci chiave...").strip()
    
    with col_p2:
        # Aggiungiamo un po' di spazio per allineare il bottone alla casella di testo
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) 
        if st.button("SBLOCCA SITO", use_container_width=True):
            # Controllo password: la rendiamo minuscola per evitare errori di battitura
            if pwd_inserita.lower() == "myplayr2026": 
                st.session_state["password_dev_corretta"] = True
                st.success("✅ Accesso autorizzato!")
                st.rerun() # Ricarica il sito mostrando il vero contenuto
            else:
                st.error("❌ Password errata!")
    
    # st.stop() blocca l'esecuzione di tutto il codice che sta SOTTO questa riga
    st.stop() 


# --- BLOCCO: LOGICA NAVIGAZIONE E SESSIONE ---

# 1. INIZIALIZZAZIONE DELLA SESSIONE (Memoria del sito)
# Definiamo tutti i valori di partenza in un colpo solo per non fare confusione
def inizializza_sessione():
    # Creiamo un elenco di impostazioni standard
    defaults = {
        'pagina': 'home',           # Pagina di partenza
        'autenticato': False,       # L'utente parte come "non collegato"
        'user_email': "",           # Email vuota all'inizio
        'user_role': "user",        # Ruolo standard: Giocatore (può diventare 'admin')
        'user_nick': "",            # Nome visualizzato dell'utente
        'editing': False            # Se l'utente sta modificando il suo profilo
    }
    
    # Controlliamo ogni voce: se non esiste ancora nella memoria (session_state), la creiamo
    for chiave, valore in defaults.items():
        if chiave not in st.session_state:
            st.session_state[chiave] = valore

# Eseguiamo subito l'inizializzazione
inizializza_sessione()

# 2. FUNZIONE DI NAVIGAZIONE
def vai_a(nome_pagina):
    """
    Cambia la pagina visualizzata sul sito e forza l'aggiornamento.
    """
    st.session_state.pagina = nome_pagina
    # Aggiungiamo st.rerun() per essere sicuri che il cambio pagina sia ISTANTANEO
    st.rerun()


# --- BLOCCO: NAVBAR DINAMICA (SINCRO SUPABASE) ---

# Mostriamo la barra di navigazione solo se l'utente ha fatto il Login
if st.session_state.autenticato:
    # 1. CONTROLLO PERMESSI: Verifichiamo se l'utente è un Admin o un Giocatore
    is_admin = st.session_state.get('user_role') == "admin"
    
    # 2. CREAZIONE COLONNE: 8 spazi se è Admin (ha il tasto segreto), 7 per gli altri
    # Usiamo col_nav per indicare le colonne della barra
    col_nav = st.columns(8 if is_admin else 7)
    
    # 3. PULSANTI DI NAVIGAZIONE (Usano la funzione vai_a del blocco precedente)
    with col_nav[0]: st.button("Home", on_click=lambda: vai_a('home_auth'), use_container_width=True, type="primary")
    with col_nav[1]: st.button("Profilo", on_click=lambda: vai_a('profilo'), use_container_width=True, type="primary")
    with col_nav[2]: st.button("Partite", on_click=lambda: vai_a('partite'), use_container_width=True, type="primary")
    with col_nav[3]: st.button("Hall of Fame", on_click=lambda: vai_a('hall_of_fame'), use_container_width=True, type="primary")
    with col_nav[4]: st.button("Le Tue Clip", on_click=lambda: vai_a('mie_clip'), use_container_width=True, type="primary")
    with col_nav[5]: st.button("Premium", on_click=lambda: vai_a('premiun'), use_container_width=True, type="primary")
    # Tasto speciale per il Gestore del Centro (Admin)
    if is_admin:
        with col_nav[5]: st.button("Admin", on_click=lambda: vai_a('admin'), use_container_width=True, type="primary")
    
    # 4. TASTO LOGOUT (Sempre nell'ultima colonna a destra)
    with col_nav[-1]: 
        if st.button("Esci", type="primary", use_container_width=True):
            # Azioni di pulizia totale quando l'utente se ne va
            st.session_state.autenticato = False
            st.session_state.user_email = ""
            st.session_state.user_role = "user"
            st.session_state.user_nick = ""
            st.session_state.pagina = 'home' # Torna alla pagina pubblica
            st.rerun() # Forza il sito a "dimenticare" i dati privati subito
            
    # Linea verde di separazione definita nel tuo CSS (hr)
    st.divider() 

# --- BLOCCO: PAGINA HOME (PUBBLICA - SUPABASE READY) ---

if st.session_state.pagina == 'home':
    # Centriamo tutto con delle colonne, mettendo il contenuto in quella centrale
    _, col_centro, _ = st.columns([1, 4, 1])
    
    with col_centro:
        # Questo è il piccolo badge che abbiamo appena creato
        st.markdown("<div style='text-align: center;'><span class='hero-badge'>✦ La rivoluzione dello sport amatoriale</span></div>", unsafe_allow_html=True)
        
        # Sotto il badge mettiamo il titolo grande (lo sistemeremo meglio dopo)
        st.markdown("<h1 style='text-align: center; font-size: 80px; font-weight: 900; line-height: 1;'>GIOCA. RIVEDITI.<br><span style='color: #2ecc71;'>CONDIVIDI.</span></h1>", unsafe_allow_html=True)
                # --- DESCRIZIONE CENTRATA ---
        st.markdown("""
            <div style='text-align: center; width: 100%;'>
                <p style='
                    color: #94a3b8; 
                    font-family: "Inter", sans-serif; 
                    font-size: 22px; 
                    line-height: 1.6; 
                    max-width: 600px; 
                    margin: 24px auto 40px auto;
                '>
                    Ogni partita merita di essere ricordata! MyClipzo <br>
                    registra automaticamente le tue azioni e ti <br>
                    permette di creare highlight professionali.
                </p>
            </div>
        """, unsafe_allow_html=True)

      # --- CTA HERO ---
        c1, c2 = st.columns(2)

        with c1:
            st.button("INIZIA GRATIS", use_container_width=True, type="primary")

        with c2:
            st.button("GUARDA DEMO", use_container_width=True, type="primary")

        st.markdown("<br>", unsafe_allow_html=True)




    # Visualizziamo i contenuti solo se l'utente non è loggato
    if not st.session_state.autenticato:
       
        # --- SEZIONE: COME FUNZIONA (LAYOUT A 3 COLONNE) ---
        # --- TITOLO E DESCRIZIONE SEZIONE CARD ---
        st.markdown("""
    <div style='text-align: center; margin-bottom: 70px;'>
        <h2 style='color: white; font-weight: 900; font-size: 40px; text-transform: uppercase; margin-bottom: 10px;'>
            COME FUNZIONA
        </h2>
        <p style='color: #94a3b8; font-size: 22px; max-width: 600px; margin: 0 auto;'>
            Un ecosistema completo per trasformare ogni partita in contenuti da professionisti.
        </p>
    </div>
""", unsafe_allow_html=True)


                # Creiamo tre colonne per mettere le schede una di fianco all'altra
        col1, col2, col3 = st.columns(3)

                # Esempio per la Colonna 1 (fai lo stesso per le altre)
        with col1:
            st.markdown("""
                <div class="mcp-card">
                    <!-- Ecco la nuova scatola dell'icona -->
                    <div class="icon-box">
                        <svg xmlns="http://w3.org" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8Z"></path><rect width="14" height="12" x="2" y="6" rx="2" ry="2"></rect></svg>
                    </div>
                    <h3 style="color: white; margin-top: 0;">REGISTRAZIONE AUTOMATICA</h3>
                    <p style="color: #94a3b8; font-size: 18px;">Il nostro sistema registra ogni partita in alta definizione 4k senza intervento manuale.</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
        <div class="mcp-card">
            <div class="icon-box">
                <!-- Disegno delle Forbici (Lucide Scissors) -->
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgb(41, 168, 71)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="6" cy="6" r="3"></circle>
                    <circle cx="6" cy="18" r="3"></circle>
                    <line x1="20" x2="8.12" y1="4" y2="15.88"></line>
                    <line x1="14.47" x2="20" y1="14.48" y2="20"></line>
                    <line x1="8.12" x2="12" y1="8.12" y2="12"></line>
                </svg>
            </div>
            <h3 style="color: white; margin-top: 0;">TAGLIO CLIP ISTANTANEO</h3>
            <p style="color: #94a3b8; font-size: 18px;">
                Seleziona il momento esatto e genera la tua clip personalizzata in pochi secondi.
            </p>
        </div>
    """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
        <div class="mcp-card">
            <div class="icon-box">
                <!-- Icona Share (Lucide Share-2) -->
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgb(41, 168, 71)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="18" cy="5" r="3"></circle>
                    <circle cx="6" cy="12" r="3"></circle>
                    <circle cx="18" cy="19" r="3"></circle>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                </svg>
            </div>
            <h3 style="color: white; margin-top: 0;">CONDIVISIONE SOCIAL</h3>
            <p style="color: #94a3b8; font-size: 18px;">
               Pubblica le tue azioni migliori nella Hall of Fame e tagga i tuoi amici sui social.
            </p>
        </div>      
    """, unsafe_allow_html=True)

        
     
            
    # --- STRISCIA DELLE STATISTICHE ---
        st.markdown("""
        <div class='stats-container'>
            <div class='stat-item'>
                <div class='stat-number'>500+</div>
                <div class='stat-label'>Partite Registrate</div>
            </div>
            <div class='stat-item'>
                <div class='stat-number'>2K+</div>
                <div class='stat-label'>Clip Generate</div>
            </div>
            <div class='stat-item'>
                <div class='stat-number'>150+</div>
                <div class='stat-label'>Giocatori Attivi</div>
            </div>
            <div class='stat-item'>
                <div class='stat-number'>4K</div>
                <div class='stat-label'>Qualità Video</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

        
        # --- SEZIONE NEWSLETTER UNIFICATA ---
        with st.form("news_form", clear_on_submit=True):
            # Titolo e Descrizione (Ora sono dentro la scatola!)
            st.markdown("<h2 style='color: white; font-weight: 900; font-size: 30px; margin-bottom: 5px; text-align: center;'>RESTA AGGIORNATO</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 18px; margin-bottom: 35px; text-align: center;'>Iscriviti alla newsletter per ricevere novità, offerte e aggiornamenti sul mondo MyClipzo</p>", unsafe_allow_html=True)

            # RIGA CON EMAIL E BOTTONE
            col_mail, col_btn = st.columns([3, 1]) # 3 parti all'email, 1 al bottone
            
            with col_mail:
                email_input = st.text_input("La tua migliore Email", placeholder="la-tua@mail.com", label_visibility="collapsed").strip().lower()
            
            with col_btn:
                submit_news = st.form_submit_button("ISCRIVITI")

            # Logica Supabase
            if submit_news:
                if "@" in email_input and "." in email_input:
                    invio_ok = invia_conferma_e_salva(email_input)
                    if invio_ok: st.success("✅ Benvenuto!")
                else:
                    st.error("❌ Email non valida.")


        # --- TASTO ACCEDI AL PORTALE (ORIGINALE) ---
        _, col_center_login, _ = st.columns([1, 2, 1])
        with col_center_login:
            st.button("ACCEDI AL PORTALE", on_click=lambda: vai_a('login'), key="home_login_btn", use_container_width=True, type="primary")


        # --- SEZIONE FINALE: CTA REGISTRAZIONE ---
        st.markdown("""
            <div class='cta-final-section'>
                <h2>PRONTO A DIVENTARE <br><span class='highlight-green'>UN CAMPIONE?</span></h2>
                <p style='font-size: 18px; !important; color: #94a3b8;'>
                    Unisciti a centinaia di giocatori che già usano MyClipzo per migliorare le proprie 
                    performance e condividere le loro migliori azioni.</p>
                
            </div>
        """, unsafe_allow_html=True)

        # Bottone Finale
        _, col_cta_btn, _ = st.columns([1, 1.5, 1])
        with col_cta_btn:
            st.button("CREA IL TUO ACCOUNT GRATIS", on_click=lambda: vai_a('login'), key="home_reg_btn", use_container_width=True, type="primary")


           # --- FOOTER A TRE COLONNE (LINK GRIGI) ---
        st.markdown("<br><hr style='border: 0.5px solid rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3, = st.columns(3)
        with f_col1:
    # Reinseriamo il logo MC stile Navbar
            st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 15px;'>
            <div class='mc-box' style='font-size: 20px; padding: 6px 10px;'>MC</div>
            <b style='color: white; font-size: 24px;'>MyClipzo</b>
        </div>
        <p style='color: #94a3b8; font-size: 20px; line-height: 1.6;'>
            La piattaforma IoT per centri sportivi. Registra, rivedi e condividi le tue migliori azioni in campo. Lo sport amatoriale come quello vero.
        </p>
        """, unsafe_allow_html=True)

        
        with f_col2:
            st.markdown("<h4 style='color: white; font-size: 24px;'>NAVIGAZIONE</h4>", unsafe_allow_html=True)
            st.button("Home", on_click=lambda: vai_a('home'), key="f_home", type="secondary")
            st.button("Partite", on_click=lambda: vai_a('partite'), key="f_part", type="secondary")
        
        with f_col3:
            st.markdown("<h4 style='color: white; font-size: 24px;'>LEGALE</h4>", unsafe_allow_html=True)
            st.button("Privacy Policy", on_click=lambda: vai_a('privacy'), key="f_priv", type="secondary")
            st.button("Termini e Condizioni", on_click=lambda: vai_a('termini'), key="f_term", type="secondary")   


# --- BLOCCO: PAGINA LOGIN / REGISTRAZIONE / RECUPERO ---

elif st.session_state.pagina == 'login':
    # Centriamo il modulo di accesso con le colonne
    _, col_log, _ = st.columns([1, 2, 1])
    
    with col_log:
        # Inizializzazione dello stato interno per navigare tra Login e Registrazione
        if 'sub' not in st.session_state: 
            st.session_state.sub = 'login'

        # --- 1. SOTTO-PAGINA: ACCEDI ---
        if st.session_state.sub == 'login':
            # Logo e Titolo come nello screenshot
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <div class='mc-box' style='display: inline-block; margin-bottom: 15px;'>MC</div>
                    <h1 style='font-weight: 900; margin-bottom: 0; color: white;'>ACCEDI A MYCLIPZO</h1>             
                </div>
            """, unsafe_allow_html=True)
            
            # Input utente
            u_login = st.text_input("Email", placeholder="la-tua@email.com").strip().lower()
            p_login = st.text_input("Password", type="password", placeholder="******")
            
            if st.button("ENTRA", use_container_width=True, type="primary"):
                if u_login and p_login:
                    try:
                        # Cerchiamo l'utente su Supabase che corrisponde a Email E Password
                        res_log = supabase.table("utenti").select("*").eq("email", u_login).eq("password", p_login).execute()
                        
                        if res_log.data:
                            # UTENTE TROVATO: Salviamo i dati nella sessione
                            utente = res_log.data[0]
                            st.session_state.autenticato = True
                            st.session_state.user_email = utente['email']
                            st.session_state.user_role = utente.get('ruolo', 'Player')
                            st.session_state.user_nick = utente.get('nome', 'Campione')
                            
                            st.success(f"Bentornato {st.session_state.user_nick}!")
                            
                            # Controllo automatico: se sei admin vai in dashboard, altrimenti in home_auth
                            if st.session_state.user_role == "admin":
                                vai_a('admin')
                            else:
                                vai_a('home_auth')
                                
                            st.rerun()
                        else:
                            st.error("❌ Credenziali errate o account inesistente.")
                    except Exception as e:
                        st.error(f"⚠️ Errore di connessione: {e}")
                else:
                    st.warning("Compila tutti i campi!")

            # Opzioni secondarie
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                if st.button("Password dimenticata?", type="secondary", use_container_width=True): 
                    st.session_state.sub = 'recupero'
                    st.rerun()
            with col_l2:
                if st.button("Registrati ora", type="secondary", use_container_width=True):
                    st.session_state.sub = 'reg'
                    st.rerun()
            
            
          # --- 2. SOTTO-PAGINA: REGISTRAZIONE (STILE MYPLAYR + LOGICA SUPABASE) ---
        elif st.session_state.sub == 'reg':
            # Logo e Titolo come nello screenshot
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <div class='mc-box' style='display: inline-block; margin-bottom: 15px;'>MC</div>
                    <h1 style='font-weight: 900; margin-bottom: 0; color: white;'>CREA IL TUO ACCOUNT</h1>
                    <p style='color: #94a3b8;'>Unisciti alla community MyClipzo</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Apertura Card Scura
            st.markdown("<div class='mcp-card'>", unsafe_allow_html=True)
            
            # Riga 1: Nome e Cognome affiancati (come nello screen)
            c1, c2 = st.columns(2)
            with c1:
                r_n = st.text_input("Nome", placeholder="", key="r_nome")
            with c2:
                r_c = st.text_input("Cognome", placeholder="", key="r_cognome")
            
            # Email e Password
            r_e = st.text_input("Email", placeholder="la-tua@mail", key="r_email").strip().lower()
            r_p = st.text_input("Password", type="password", placeholder="Scegli una password", key="r_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # BOTTONE PRINCIPALE (La tua logica Supabase integrata)
            if st.button("CREA ACCOUNT", use_container_width=True, type="primary", key="btn_confirm_reg"):
                if r_n and r_c and r_e and r_p:
                    try:
                        nuovo_utente = {
                            "nome": r_n, "cognome": r_c, 
                            "email": r_e, "password": r_p, 
                            "ruolo": "Player"
                        }
                        supabase.table("utenti").insert(nuovo_utente).execute()
                        st.success("✅ Account creato con successo! Ora puoi accedere.")
                        st.session_state.sub = 'login'
                        st.rerun()
                    except Exception as e:
                        st.error("Errore: Email già registrata o problema tecnico.")
                else: 
                    st.error("⚠️ Inserisci tutti i dati richiesti!")
            
            # Navigazione interna alla card
            st.markdown("<hr style='opacity: 0.1; margin: 20px 0;'><p style='text-align: center; color: #94a3b8; font-size: 14px;'>Hai già un account?</p>", unsafe_allow_html=True)
            
            if st.button("ACCEDI", use_container_width=True,type="primary", key="btn_back_to_log"): 
                st.session_state.sub = 'login'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True) # Chiusura Card

         

        # --- 3. SOTTO-PAGINA: RECUPERO PASSWORD ---
        elif st.session_state.sub == 'recupero':
            st.markdown("<h2 style='text-align: center;'>Recupero Credenziali</h2>", unsafe_allow_html=True)
            m_rec = st.text_input("La tua Email di registrazione").strip().lower()
            
            if st.button("INVIA ISTRUZIONI", use_container_width=True,type="primary"):
                if m_rec:
                    st.info(f"Se l'account esiste, riceverai una mail a {m_rec} (Funzione in test)")
                else:
                    st.warning("Inserisci un'email!")
            
            if st.button("← TORNA AL LOGIN", type="secondary", use_container_width=True): 
                st.session_state.sub = 'login'
                st.rerun()
        
# --- BLOCCO: PAGINA ADMIN (DASHBOARD SUPABASE) ---

elif st.session_state.pagina == 'admin':
    
    # 1. RECUPERO CONTEGGI REALI (Cloud)
    try:
        # Conteggio utenti registrati
        res_u = supabase.table("utenti").select("id", count="exact").execute()
        num_utenti = res_u.count if res_u.count else 0
        
        # Conteggio partite totali nel database
        res_p = supabase.table("calendario").select("id", count="exact").execute()
        num_partite = res_p.count if res_p.count else 0
        
        # Conteggio iscritti alla newsletter
        res_n = supabase.table("newsletter").select("id", count="exact").execute()
        num_newsletter = res_n.count if res_n.count else 0
    except Exception as e:
        st.error(f"Errore caricamento dati statistici: {e}")
        num_utenti = num_partite = num_newsletter = 0

    st.title("📊 Dashboard Amministratore")

    # 2. RIGA DEI CONTATORI (Metriche veloci)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("⚽ Partite", num_partite)
    with c2: st.metric("👥 Giocatori", num_utenti)
    with c3: st.metric("📧 Newsletter", num_newsletter)
    with c4: st.metric("🎞️ Clip Generate", "0") # Dato da collegare alla tabella 'clip_generate'
    with c5: st.metric("💰 Ricavi Est.", "€0.00")

    st.divider()

    # 3. GRAFICO E AZIONI RAPIDE
    col_graf, col_act = st.columns([1.5, 1]) # Grafico più largo per leggibilità
    
    with col_graf:
        st.subheader("📈 Attività Settimanale")
        # Dati simulati per il grafico (in futuro potrai renderli reali)
        dati_grafico = pd.DataFrame({
            "Giorno": ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"], 
            "Partite": [2, 5, 4, 8, 6, 12, 10]
        })
        st.line_chart(dati_grafico, x="Giorno", y="Partite", color="#28a745")
    
    with col_act:
        st.subheader("⚡ Azioni Rapide")
        # Layout compatto per i bottoni
        if st.button("📥 Export Utenti (CSV)", use_container_width=True):
            try:
                res_export = supabase.table("utenti").select("*").execute()
                df_export = pd.DataFrame(res_export.data)
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Scarica File CSV", csv, "utenti_myplayr.csv", "text/csv")
            except:
                st.error("Errore durante l'export.")
        
        st.button("📧 Invia Newsletter Massiva", use_container_width=True)
        st.button("📊 Genera Report Mensile", use_container_width=True)
        if st.button("🧹 Svuota Cache Sistema", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache pulita!")

    st.divider()

    # 4. ARCHIVIO REGISTRAZIONI (Gestione Video)
    st.subheader("🎞️ Archivio Video Master (4K)")
    
    try:
        # Recuperiamo i match completati ordinati dal più recente
        res_video = supabase.table("calendario")\
            .select("*")\
            .eq("stato", "FATTO")\
            .order("id", desc=True)\
            .execute()
        
        partite_fatte = res_video.data

        if partite_fatte:
            for partita in partite_fatte:
                # Creiamo un contenitore pulito per ogni partita
                with st.expander(f"📅 {partita['data']} - {partita['campo']} ({partita['ora']})"):
                    col_v_info, col_v_video = st.columns([1, 2])
                    
                    with col_v_info:
                        st.write(f"📄 **File:** `{partita['evento']}`")
                        st.write(f"🆔 **ID Match:** {partita['id']}")
                        
                        # Tasto eliminazione con conferma
                        if st.checkbox(f"Conferma eliminazione ID {partita['id']}", key=f"chk_{partita['id']}"):
                            if st.button(f"🔴 ELIMINA DEFINITIVAMENTE", key=f"del_{partita['id']}", type="primary"):
                                supabase.table("calendario").delete().eq("id", partita['id']).execute()
                                st.warning(f"Record {partita['id']} eliminato.")
                                st.rerun()
                    
                    with col_v_video:
                        _v = make_direct_link(partita.get("link_video"))
                        if _v:
                            st.video(_v)
                        else:
                            st.info("Video non ancora caricato sul Cloud.")
        else:
            st.info("Nessuna registrazione completata trovata nel database.")
            
    except Exception as e:
        st.error(f"Errore nel caricamento dell'archivio: {e}")

    # 5. RICHIESTE CLIP DAGLI UTENTI (Monitoraggio)
    st.divider()
    st.subheader("📩 Richieste Clip in Attesa")
    # Qui leggeremo la tabella dei comandi inviati dagli utenti
    st.info("Al momento non ci sono richieste manuali di taglio clip in sospeso.")


    # --- BLOCCO: PROGRAMMAZIONE REGISTRAZIONE (ADMIN - SUPABASE READY) ---

    st.divider()

    # Usiamo un expander per non occupare spazio prezioso nella Dashboard
    with st.expander("📅 PROGRAMMA NUOVA REGISTRAZIONE 🎥", expanded=False):
        st.markdown("<p style='font-size: 14px;'>Inserisci i dettagli del match. Il Mini PC in campo riceverà l'ordine in tempo reale.</p>", unsafe_allow_html=True)
        
        with st.form("form_admin_reg", clear_on_submit=True):
            # 1. INPUT DATI
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_gara = st.date_input("Giorno della Gara", datetime.now())
            with col_d2:
                ora_gara = st.text_input("Ora Inizio (es: 19:30)", placeholder="HH:MM")
                
            titolo_match = st.text_input("Titolo Partita (es: Squadra A vs Squadra B)")
            campo_selezionato = st.selectbox("Seleziona Campo", ["Campo A (Calcio a 5)", "Campo B (Padel)", "Campo C (Calcio a 7)"])
            
            # 2. BOTTONE DI CONFERMA
            if st.form_submit_button("CONFERMA E PROGRAMMA REGISTRAZIONE", use_container_width=True):
                if ora_gara and titolo_match:
                    
                    # --- AGGIUNTA SICUREZZA: Pulizia automatica orario ---
                    ora_pulita = ora_gara.strip()
                    # Se scrivi 9:30, lo trasformiamo in 09:30 per il Mini PC
                    if len(ora_pulita) == 4 and ":" in ora_pulita:
                        ora_pulita = "0" + ora_pulita
                    
                    # Prepariamo l'oggetto per Supabase
                    nuovo_match = {
                        "data": data_gara.strftime('%d-%m-%Y'),
                        "ora": ora_pulita,  # Usiamo l'ora pulita
                        "campo": campo_selezionato,
                        "evento": titolo_match.strip(),
                        "stato": "PROGRAMMATO"
                    }
                    
                    try:
                        # Invio dati al Cloud
                        supabase.table("calendario").insert(nuovo_match).execute()
                        
                        st.success(f"✅ Gara '{titolo_match}' programmata con successo!")
                        # Aspettiamo un istante per far vedere il messaggio e poi ricarichiamo
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Errore durante il salvataggio sul Cloud: {e}")
                else:
                    st.warning("⚠️ Per favore, inserisci almeno l'orario e il titolo della partita.")


    # --- BLOCCO: ARCHIVIO VIDEO TOTALE (VISTA TABELLARE PER ADMIN) ---

            st.divider()
            st.subheader("📊 Riepilogo Attività Video")

    # 1. ARCHIVIO PARTITE INTERE (Tutto ciò che il Mini PC ha registrato)
            st.markdown("#### 🏟️ Match Registrati (Master 4K)")

    try:
        # Recuperiamo i dati delle partite concluse (stato 'FATTO')
        res_vids = supabase.table("calendario")\
            .select("id, data, ora, campo, evento")\
            .eq("stato", "FATTO")\
            .order("id", desc=True)\
            .execute()
        
        if res_vids.data:
            df_vids = pd.DataFrame(res_vids.data)
            
            # --- MODIFICA SICURA QUI ---
            # Questo controllo evita che il sito crashi se mancano dati
            colonne_da_mostrare = [c for c in ['id', 'data', 'ora', 'campo', 'evento'] if c in df_vids.columns]
            
            st.dataframe(
                df_vids[colonne_da_mostrare], 
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "data": "Data Gara",
                    "ora": "Orario",
                    "campo": "Campo",
                    "evento": "Descrizione Match"
                },
                hide_index=True
            )
        # --- FINE MODIFICA ---

        else:
            st.info("ℹ️ Nessuna partita intera registrata al momento.")

    except Exception as e:
        st.error(f"Errore caricamento tabella partite: {e}")

    st.write("<br>", unsafe_allow_html=True)

    

    # --- BLOCCO: GESTIONE RAPIDA ARCHIVIO (CANCELLAZIONE ADMIN) ---

    st.divider()
    st.subheader("🗑️ Pulizia Rapida Archivio")
    st.markdown("<p style='font-size: 13px; color: #888;'>Usa questa sezione per rimuovere i match obsoleti o errati dal portale.</p>", unsafe_allow_html=True)

    # --- MODIFICA DI SICUREZZA: Controlliamo se df_vids esiste davvero prima di usarlo ---
    if 'df_vids' in locals() and not df_vids.empty:
        for idx, row in df_vids.iterrows():
            # Da qui in poi il tuo codice originale (c1, c2, c3...) continua uguale
            c1, c2, c3, c4, c5 = st.columns([1.2, 1.5, 1, 3, 0.8])
            
            c1.write(f"📅 **{row['data']}**")
            c2.write(f"🏟️ {row['campo']}")
            c3.write(f"🕒 {row['ora']}")
            
            # Mostriamo il titolo o un segnaposto se vuoto
            titolo_gara = row['evento'] if row['evento'] else "Senza Titolo"
            c4.write(f"📝 {titolo_gara}")
            
            # TASTO CANCELLA con chiave unica basata sull'ID del database
            if c5.button("🗑️", key=f"btn_del_{row['id']}", help="Elimina definitivamente questo record"):
                # --- LOGICA DI CANCELLAZIONE SICURA ---
                try:
                    # 1. Comando di eliminazione su Supabase
                    supabase.table("calendario").delete().eq("id", row['id']).execute()
                    
                    # 2. Feedback visivo per l'Admin
                    st.toast(f"✅ Match #{row['id']} rimosso con successo!", icon='🗑️')
                    
                    # 3. Aspettiamo un attimo per dare tempo al database di aggiornarsi
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Impossibile eliminare il record: {e}")
    else:
        st.info("📂 L'archivio è attualmente vuoto. Nessun dato da gestire.")

    st.divider()

            # --- BLOCCO: PAGINA GESTIONE PARTITE E COMANDI CLIP (SUPABASE) ---

    if st.session_state.pagina == "Admin":
        st.title("⚙️ Controllo Operativo MyClipzo")
        
        # 1. FORM PROGRAMMAZIONE REGISTRAZIONE
        # Serve per dire al Mini PC: "A quest'ora accendi la camera"
        with st.expander("📅 PROGRAMMA NUOVO MATCH", expanded=True):
            with st.form("programma_match", clear_on_submit=True):
                col_d, col_o = st.columns(2)
                with col_d:
                    data_p = st.date_input("Data Evento", datetime.now())
                with col_o:
                    ora_p = st.text_input("Ora Inizio (es. 20:30)", placeholder="HH:MM")
                
                campo_p = st.selectbox("Seleziona Campo", ["Campo A", "Campo B", "Campo C", "Padel 1"])
                titolo_p = st.text_input("Squadre / Titolo Partita", placeholder="es. Rossi vs Bianchi")

                if st.form_submit_button("🔴 CONFERMA PROGRAMMAZIONE", use_container_width=True):
                    if ora_p and titolo_p:
                        try:
                            supabase.table("calendario").insert({
                                "data": data_p.strftime("%d-%m-%Y"),
                                "ora": ora_p.strip(),
                                "campo": campo_p,
                                "evento": titolo_p.strip(),
                                "stato": 'PROGRAMMATO' # Segnale per il Mini PC
                            }).execute()
                            st.success(f"✅ Registrazione programmata con successo!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore database: {e}")
                    else:
                        st.warning("Completa tutti i campi prima di confermare.")

        st.divider()


# --- BLOCCO DASHBOARD UTENTE ---
elif st.session_state.pagina == 'home_auth':

    st.markdown(f"""
        <h1 style='font-size: 50px; font-weight: 900;'>
            👋 Benvenuto, <span style='color:#2ecc71;'>{st.session_state.user_nick}</span>
        </h1>
        <p style='color:#94a3b8; font-size:18px;'>
            Ecco cosa sta succedendo nel tuo mondo MyClipzo oggi.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
                <div class="mcp-card">
                    <!-- Ecco la nuova scatola dell'icona -->
                    <div class="icon-box">
                        <svg xmlns="http://w3.org" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8Z"></path><rect width="14" height="12" x="2" y="6" rx="2" ry="2"></rect></svg>
                    </div>
                    <h3 style="color: white; margin-top: 0;">le tue clip</h3>
                    <p style="color: #94a3b8; font-size: 18px;">Il nostro sistema registra ogni partita in alta definizione 4k senza intervento manuale.</p>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='stat-card'>
                <h2>⚽</h2>
                <h1>8</h1>
                <p>Partite giocate</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class='stat-card'>
                <h2>🔥</h2>
                <h1>24</h1>
                <p>Azioni salvate</p>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class='stat-card'>
                <h2>🏆</h2>
                <h1>#15</h1>
                <p>Rank</p>
            </div>
        """, unsafe_allow_html=True)   
    st.markdown("<br><h2>🏟️ Ultime Partite</h2>", unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    with col_v2:
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    st.markdown("<br><h2>🚀 Azioni Veloci</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    st.markdown("<br><h2>🔥 Le Tue Migliori Clip</h2>", unsafe_allow_html=True)

    col_c1, col_c2, col_c3 = st.columns(3)

    for col in [col_c1, col_c2, col_c3]:
        with col:
            st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    with c1:
        st.button("🎥 Guarda Partite", use_container_width=True,
                  on_click=lambda: vai_a('partite'))

    with c2:
        st.button("✂️ Le Mie Clip", use_container_width=True,
                  on_click=lambda: vai_a('mie_clip'))

    with c3:
        st.button("👤 Profilo", use_container_width=True,
                  on_click=lambda: vai_a('profilo'))

  
        
# --- BLOCCO PROFILO: VERSIONE INTEGRALE E CORRETTA ---
elif st.session_state.pagina == 'profilo':
    st.markdown("<h1 style='text-align: center;'>Area Personale<br><span style='color: #2ecc71;'>MyClipzo</span></h2>", unsafe_allow_html=True)
    
    try:
        import time
        email_sessione = st.session_state.user_email.strip().lower()
        
        # 1. Recupero dati Utente (FIX: single record)
        res_u = supabase.table("utenti").select("*").eq("email", email_sessione).maybe_single().execute()
        user = res_u.data
        
        if user:
            # --- SEZIONE A: MODIFICA DATI ---
            with st.expander("Modifica Dati e Carica Foto"):
                col_f, col_i = st.columns(2)
                with col_f:
                    st.write(" **La tua Foto**")
                    foto_file = st.file_uploader("Scegli file", type=['png', 'jpg', 'jpeg'], key="up_p")
                    
                    # Visualizzazione foto attuale
                    f_path = user.get('foto_path')
                    if foto_file: 
                        st.image(foto_file, width=100)
                    elif f_path: 
                        st.image(f"{f_path}?t={int(time.time())}", width=80)
                
                with col_i:
                    v_nick = st.text_input("Nickname", value=user.get('nickname') or "")
                    v_ig = st.text_input("Instagram", value=user.get('ig_tag') or "")
                    ruoli = ["Attaccante", "Centrocampista", "Difensore", "Portiere", "Padel Player"]
                    v_ruolo = st.selectbox("Ruolo", ruoli, index=ruoli.index(user.get('ruolo')) if user.get('ruolo') in ruoli else 0)
                    v_bio = st.text_area("La tua Bio", value=user.get('bio') or "")

                if st.button("SALVA TUTTE LE MODIFICHE", use_container_width=True, type="primary"):
                    dati_agg = {"nickname": v_nick, "ig_tag": v_ig, "ruolo": v_ruolo, "bio": v_bio}
                    
                    if foto_file:
                        try:
                            nome_f = f"avatar_{user['id']}.jpg"
                            # Caricamento REALE nello storage di Supabase
                            supabase.storage.from_("foto_profili").upload(
                                path=nome_f, 
                                file=foto_file.getvalue(), 
                                file_options={"content-type": "image/jpeg", "x-upsert": "true"}
                            )
                            dati_agg["foto_path"] = supabase.storage.from_("foto_profili").get_public_url(nome_f)
                        except Exception as e_f:
                            st.error(f"Errore caricamento foto: {e_f}")

                    # Aggiornamento Database
                    supabase.table("utenti").update(dati_agg).eq("email", email_sessione).execute()
                    st.success("✅ Dati salvati!")
                    time.sleep(1)
                    st.rerun()

            st.divider()

            # --- SEZIONE B: VISUALIZZAZIONE DATI ---
            cl, cr = st.columns(2)
            with cl:
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                f_p = user.get('foto_path')
                if f_p: 
                    st.image(f"{f_p}?t={int(time.time())}", width=150)
                else: 
                    st.markdown('<div style="font-size:80px; background:#3E444A; border-radius:50%; padding:20px; display:inline-block;">👤</div>', unsafe_allow_html=True)
                st.markdown(f"<h4>{user.get('nome', 'Atleta')}</h4>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with cr:
                st.markdown(f'<div style="background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745; margin-bottom:10px;"><b>Nickname:</b> {user.get("nickname") or "N/A"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745; margin-bottom:10px;"><b>Instagram:</b> {user.get("ig_tag") or "N/A"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745; margin-bottom:10px;"><b>Ruolo:</b> {user.get("ruolo") or "Player"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745; margin-bottom:10px;"><b>Email:</b> {email_sessione}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745;"><b>Bio:</b> {user.get("bio") or "Nessuna bio"}</div>', unsafe_allow_html=True)

            # --- SEZIONE C: LE MIE CLIP (FIX: recupero video) ---
            st.divider()
            st.subheader("🎥 I Tuoi Highlight")
            # Cerchiamo clip dove l'utente è il proprietario (campo campo = email)
            res_c = supabase.table("calendario").select("*").eq("stato", "CLIP_UTENTE").eq("campo", email_sessione).execute()
            
            if res_c.data:
                cols_v = st.columns(2)
                for i, clip in enumerate(res_c.data):
                    with cols_v[i % 2]:
                        v_u = make_direct_link(clip.get("link_video"))
                        if v_u:
                            st.video(v_u)
            else: 
                st.info("📺 Nessuna clip salvata nel tuo archivio.")

            # --- SEZIONE D: STATISTICHE ---
            st.divider()
            st.subheader("Statistiche Personali")
            s_cols = st.columns(6)
            stats = [("🎞️","Clip", len(res_c.data)), ("⚽","Goal", "0"), ("👟","Assist", "0"), ("🏆","Rank", "-"), ("🏅","Badge", "0"), ("🔥","Azioni", "0")]
            for i, (ico, tit, val) in enumerate(stats):
                with s_cols[i]: 
                    st.markdown(f'<div style="text-align:center; background:#3E444A; font-size:25px; padding:20px; border-radius:10px; border:1px solid #28a745;">{ico}<br><small>{tit}</small><br><b>{val}</b></div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("I tuoi badge")
            st.info("🏅 Partecipa a più partite per sbloccare i tuoi primi badge!")

        else: 
            st.error("⚠️ Utente non trovato nel database.")
            
    except Exception as e:
        st.error(f"Errore tecnico nel profilo: {e}")


# --- PAGINA PARTITE (VERSIONE SINCRONIZZATA CON REGISTA.PY) ---
elif st.session_state.pagina == 'partite':
    import streamlit.components.v1 as components
    import pandas as pd
    
    st.title("Archivio Partite")
    st.write("Guarda i match registrati e richiedi il taglio delle tue azioni migliori.")

    try:
        # 1. Recupero partite concluse (Stato 'FATTO' impostato dal Regista)
        res_matches = supabase.table("calendario")\
            .select("*")\
            .eq("stato", "FATTO")\
            .order("id", desc=True)\
            .execute()
        
        partite = res_matches.data if res_matches.data else []

        if not partite:
            st.info("📌 Al momento non ci sono partite registrate disponibili.")
        else:
            for partita in partite:
                st.subheader(f"🏟️ {partita.get('evento')} - {partita.get('data')}")
                
                # Il regista.py salva il link direttamente in 'link_video' 
                video_url = partita.get("link_video")

                if video_url:
                    # Visualizzazione Player (Il link è già /preview grazie al Regista)
                    components.iframe(video_url, height=480, scrolling=False)
                    
                    # Tasto per apertura esterna (sostituiamo /preview con /view al volo)
                    url_esterno = video_url.replace("/preview", "/view")
                    st.link_button("▶️ GUARDA A TUTTO SCHERMO", url_esterno, use_container_width=True)

                    # 2. MODULO TAGLIO CLIP (Invia comandi a 'comandi_clip' per il Mini PC)
                    with st.expander("TAGLIA LA TUA CLIP"):
                        st.write("Indica il minuto esatto dell'azione nel video:")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            m_in = st.number_input("Minuto", min_value=0, max_value=120, key=f"m_{partita['id']}")
                        with c2:
                            s_in = st.number_input("Secondo", min_value=0, max_value=59, key=f"s_{partita['id']}")
                        with c3:
                            dur = st.number_input("Durata (sec)", min_value=5, max_value=60, value=15, key=f"d_{partita['id']}")

                        if st.button("GENERA CLIP", key=f"btn_{partita['id']}", use_container_width=True):
                            start_sec = (m_in * 60) + s_in
                            try:
                                supabase.table("comandi_clip").insert({
                                    "id_partita": partita['id'],
                                    "inizio_secondi": start_sec,
                                    "durata_secondi": dur,
                                    "email_utente": st.session_state.user_email,
                                    "stato": "RICHIESTO"
                                }).execute()
                                st.success("✅ Comando inviato! Il Mini PC sta elaborando il taglio.")
                            except Exception as e:
                                st.error(f"Errore: {e}")
                else:
                    st.warning("⏳ Elaborazione video in corso...")
                
                st.divider()

    except Exception as e:
        st.error(f"⚠️ Errore caricamento: {e}")

# --- 3. PAGINA: LE MIE CLIP (DOVE L'UTENTE GUARDA I VIDEO TAGLIATI) ---
elif st.session_state.pagina == 'mie_clip':
    st.title("Le Mie Clip Personalizzate")
    st.write("Qui trovi i momenti migliori delle tue partite, tagliati e pronti da condividere!")

    try:
        # Recuperiamo solo le clip dell'utente loggato che sono state COMPLETATE dal PC
        res_clip = supabase.table("comandi_clip")\
            .select("*")\
            .eq("email_utente", st.session_state.user_email)\
            .eq("stato", "COMPLETATO")\
            .order("id", desc=True)\
            .execute()

        mie_clip = res_clip.data if res_clip.data else []

        if not mie_clip:
            st.info("📌 Non hai ancora clip pronte. Richiedine una dalla sezione 'Partite' e attendi che il Mini PC la elabori (circa 2-3 minuti).")
        else:
            # Mostriamo i video uno sotto l'altro
            for clip in mie_clip:
                with st.container():
                    st.subheader(f"Richiesta del {clip.get('created_at')[:10]}")
                    
                    # Prendiamo l'URL che il Mini PC ha caricato su Drive
                    url_video = clip.get("url_video")
                    
                    if url_video:
                        # Player Video (Iframe di Google Drive)
                        st.components.v1.iframe(url_video, height=450, scrolling=False)
                        
                        # Tasto per download o visione esterna
                        st.link_button("🔗 Scarica o Condividi Clip", url_video.replace("/preview", "/view"), use_container_width=True)
                    else:
                        st.warning("⏳ Elaborazione in corso...")
                    st.divider()

    except Exception as e:
        st.error(f"Errore nel caricamento delle clip: {e}")


# --- PAGINA PRIVACY POLICY ---
elif st.session_state.pagina == 'privacy':
    st.markdown("<h1 style='text-align: center; color: white;'>PRIVACY E POLICY</h1>", unsafe_allow_html=True)
    
    # Incolla il tuo testo tra le triple virgolette
    testo_privacy = """ 
        

1. Titolare del Trattamento: Il titolare è MyClipzo (email: privacy@myclipzo.com). Per i servizi presso i centri sportivi, MyClipzo agisce come Responsabile Esterno o Contitolare insieme alla Struttura Ospitante.
2. Tipologia di dati raccolti: Nome, cognome, email, username, dati tecnici di navigazione e contenuti video/immagini generati durante l'attività sportiva.
3. Finalità del trattamento: Registrazione, accesso all'area personale, generazione/download delle clip e condivisione volontaria sui social. I video sono trattati esclusivamente per scopi sportivi e ricreativi.
4. Base giuridica: Il trattamento avviene sulla base dell'esecuzione del contratto (erogazione servizio) e del consenso esplicito dell'utente.
5. Conservazione dei dati: I dati dell'account restano attivi fino a richiesta di cancellazione. I file video originali vengono conservati per un massimo di 60 giorni, dopodiché vengono eliminati definitivamente per ragioni di storage.
6. Condivisione dei dati: I dati non sono venduti a terzi. Sono accessibili solo ai partner tecnologici necessari (es. Cloud Storage, Database) vincolati al segreto professionale.
7. Diritti dell’utente: Accesso, rettifica, cancellazione (oblio) e revoca del consenso inviando una mail a: privacy@myclipzo.com.
8. Sicurezza: Adottiamo protocolli di crittografia e accesso sicuro (2FA) per proteggere i flussi video.

    """
    
    st.markdown(f"<div style='text-align: justify; font-size: 24px; color: white;'>{testo_privacy}</div>", unsafe_allow_html=True)

# --- PAGINA DIRITTI RISERVATI ---
elif st.session_state.pagina == 'diritti':
    st.markdown("<h2 style='text-align: center; color: white;'>DIRITTI RISERVATI</h2>", unsafe_allow_html=True)
    
    testo_diritti = """
    Proprietà dei Contenuti e Diritti Riservati:
    Tutti i contenuti presenti su questo sito, inclusi testi, grafica, loghi, icone, immagini e il software di gestione, sono di proprietà esclusiva di MyClipzo o dei suoi licenzianti e sono protetti dalle leggi internazionali sul diritto d'autore.
Riprese Video e Clip:
Le riprese effettuate durante gli eventi sportivi hanno finalità di analisi tecnica e documentazione amatoriale. I diritti relativi alle immagini appartengono a MyClipzo, fermo restando il diritto all'immagine dei partecipanti.
Limitazioni d'uso:
È severamente vietata la riproduzione, la modifica, la distribuzione, la trasmissione o la pubblicazione dei video e delle clip presenti nel sito per scopi commerciali senza l'espressa autorizzazione scritta di MyClipzo. L'utente ha il diritto di visualizzare e scaricare le proprie clip esclusivamente per uso personale e privato (social network inclusi, previo tag della pagina ufficiale).
© 2026 MyClipzo - Tutti i diritti riservati.
    """
    
    st.markdown(f"<div style='color: white; font-size: 24px; text-align: justify;'>{testo_diritti}</div>", unsafe_allow_html=True)
    
    

# --- PAGINA TERMINI E CONDIZIONI ---
elif st.session_state.pagina == 'termini':
    st.markdown("<h1 style='text-align: center; color: white;'>TERMINI E CONDIZIONI</h1>", unsafe_allow_html=True)
    
    # Incolla il tuo testo tra le triple virgolette
    testo_termini = """
   

1. Descrizione del servizio -
    Piattaforma digitale per la fruizione di clip video generate in strutture partner. Il servizio è fornito "così com'è" per scopi di intrattenimento.

2. Registrazione -
    L'utente dichiara di avere almeno 18 anni o di possedere il consenso dei genitori.

3. Utilizzo delle clip -
    Le clip sono per uso personale. La condivisione sui social è una scelta libera e consapevole dell'utente.

4. Responsabilità dell’utente -
    È vietato l'uso delle clip per scopi diffamatori, illegali o per ledere la dignità altrui. L'utente è l'unico responsabile dei contenuti pubblicati.

5. Limitazione di responsabilità -
    MyClipzo non garantisce la continuità del servizio in caso di guasti tecnici o mancanza di rete nel centro sportivo. Le riprese non hanno valore legale o arbitrale e non possono essere usate in procedimenti disciplinari o civili.

6. Sospensione - 
    Ci riserviamo di chiudere account che violano le regole di community o caricano contenuti impropri.

7. Foro competente - 
    Per ogni controversia è competente il Foro di [Tua Città], Italia.

    """
    
    st.markdown(f"<div style='text-align: justify; font-size: 24px;color: white;'>{testo_termini}</div>", unsafe_allow_html=True)
    
# --- PAGINA DIRITTI RISERVATI ---
elif st.session_state.pagina == 'diritti':
    st.markdown("<h2 style='text-align: center; color: white;'>DIRITTI RISERVATI</h2>", unsafe_allow_html=True)
    

# --- BLOCCO: PAGINA HALL OF FAME PRO (FIXED) ---

if st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>HALL OF FAME</h1>", unsafe_allow_html=True)
    st.divider()

    try:
        # 1. RECUPERO DATI CON JOIN
        res_pro = supabase.table("calendario")\
            .select("id, evento, campo, consenso_social, stato, link_video, utenti(nome, ig_tag)")\
            .eq("stato", "CLIP_UTENTE")\
            .eq("consenso_social", 1)\
            .order("id", desc=True)\
            .execute()
        
        dati_fame = res_pro.data if res_pro.data else []

        if dati_fame:
            gia_visti = []
            
            for clip in dati_fame:
                url_v = clip.get('link_video')
                nome_f = clip.get('evento', 'clip.mp4')
                
                if nome_f in gia_visti or not url_v:
                    continue
                
                link_per_player = make_direct_link(url_v)
                if not link_per_player:
                    continue

                # --- VISUALIZZAZIONE ---
                with st.container():
                    st.video(link_per_player)
                    gia_visti.append(nome_f)
                    
                    # Recupero dati dell'autore (gestione sicura se Supabase restituisce una lista)
                    info_u = clip.get('utenti')
                    if isinstance(info_u, list): info_u = info_u[0] # Prende il primo se è una lista
                    
                    # Nome Atleta
                    autore = info_u.get('nome') if info_u and info_u.get('nome') else clip['campo']
                    st.success(f"⚽ **Protagonista: {autore}**")
                    
                    # Tag Instagram
                    ig = info_u.get('ig_tag') if info_u else None
                    if ig:
                        st.caption(f"📸 Instagram: **{ig}**")
                    
                    st.divider()
        else:
            st.info("📌 La Hall of Fame è in attesa dei primi campioni! Dai il consenso in 'Le Mie Clip'.")

    except Exception as e:
        # Se la JOIN fallisce per mancanza di relazione, mostriamo un messaggio pulito
        st.warning("⚠️ Stiamo sincronizzando i profili degli atleti. I video saranno visibili a breve!")
        print(f"Errore JOIN: {e}")


# --- TASTO DI RITORNO SICURO ---
if st.session_state.pagina not in ['home', 'home_auth']:
    if st.button("← Torna alla Home", key="btn_ritorno_universale"):
        # RESETTA IL SOTTOMENU: Questa è la riga fondamentale!
        st.session_state.sub = 'login' 
        
        if st.session_state.get('autenticato', False):
            st.session_state.pagina = 'home_auth'
        else:
            st.session_state.pagina = 'home'
        st.rerun()

# --- COPYRIGHT CLICCABILE NEL FOOTER ---
st.markdown("<br>", unsafe_allow_html=True) # Un po' di spazio

if st.button(f"© 2026 MyClipzo - Tutti i diritti riservati", key="f_copy_btn", use_container_width=True):
    st.session_state.pagina = 'diritti'
    st.rerun()






