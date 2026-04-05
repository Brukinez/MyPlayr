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
    :root {
        --bg-main: #0f141a;
        --bg-panel: #19212b;
        --bg-soft: #24303d;
        --text-main: #f5f7fb;
        --text-soft: #c4d0dc;
        --neon: #24e170;
        --neon-strong: #17c95f;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% -10%, rgba(36, 225, 112, 0.18), transparent 35%),
            radial-gradient(circle at 90% 0%, rgba(36, 225, 112, 0.10), transparent 28%),
            linear-gradient(180deg, #111821 0%, var(--bg-main) 100%);
        color: var(--text-main);
    }

    [data-testid="stHeader"] {
        background: rgba(15, 20, 26, 0.75);
        backdrop-filter: blur(6px);
        border-bottom: 1px solid rgba(36, 225, 112, 0.20);
    }

    h1, h2, h3, h4, h5, p, span, label, li, .stMarkdown {
        color: var(--text-main) !important;
    }

    .stApp a {
        color: var(--neon) !important;
    }

    .stApp hr {
        border: 1px solid rgba(36, 225, 112, 0.50) !important;
        opacity: 1;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #121a23 0%, #0f141a 100%);
        border-right: 1px solid rgba(36, 225, 112, 0.16);
    }

    /* Bottoni principali verde neon */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, var(--neon) 0%, var(--neon-strong) 100%) !important;
        color: #03160b !important;
        border: 1px solid #2aff8b !important;
        font-weight: 800 !important;
        letter-spacing: 0.4px;
        width: 100%;
        padding: 12px 16px;
        border-radius: 12px;
        text-transform: uppercase;
        font-size: 15px;
        box-shadow:
            0 0 0 1px rgba(36, 225, 112, 0.25),
            0 8px 24px rgba(36, 225, 112, 0.28);
        transition: all 0.2s ease;
    }

    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        filter: brightness(1.05);
        box-shadow:
            0 0 0 1px rgba(42, 255, 139, 0.45),
            0 10px 28px rgba(36, 225, 112, 0.38);
    }

    /* Bottoni secondari trasparenti */
    div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: transparent !important;
        color: var(--text-soft) !important;
        border: 1px solid rgba(196, 208, 220, 0.30) !important;
        border-radius: 10px;
        font-size: 13px !important;
        text-transform: none !important;
    }

    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        color: var(--neon) !important;
        border-color: rgba(36, 225, 112, 0.65) !important;
        background-color: rgba(36, 225, 112, 0.08) !important;
    }

    /* Input e uploader con bordo neon */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea textarea,
    .stNumberInput input,
    [data-testid="stFileUploaderDropzone"] {
        background: var(--bg-panel) !important;
        color: var(--text-main) !important;
        border: 1px solid rgba(36, 225, 112, 0.30) !important;
        border-radius: 10px !important;
    }

    .stFileUploader label {
        color: var(--neon) !important;
        font-weight: 700 !important;
    }

    /* Card personalizzate */
    .data-card, .stat-box {
        background: linear-gradient(180deg, #202b37 0%, var(--bg-panel) 100%);
        border: 1px solid rgba(36, 225, 112, 0.25);
        border-left: 4px solid var(--neon);
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.24);
    }

    .data-card {
        padding: 15px;
        margin-bottom: 10px;
        font-size: 14px;
    }

    .stat-box {
        text-align: center;
        padding: 15px;
    }

    .avatar-container { text-align: center; margin-bottom: 20px; }
    .avatar-img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 3px solid var(--neon);
        box-shadow: 0 0 28px rgba(36, 225, 112, 0.22);
        object-fit: cover;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-soft);
        font-size: 60px;
    }

    .footer-main {
        text-align: center;
        font-size: 16px;
        margin-top: 50px;
    }

    .footer-sub {
        font-size: 12px;
        color: #8aa0b5;
    }
</style>
"""

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

# Creazione automatica cartelle mancanti
for cartella in [VIDEO_DIR, IMG_DIR, CLIP_DIR]:
    if not os.path.exists(cartella):
        os.makedirs(cartella)

# --- 3. COSTANTI ---
GRANDEZZA_LOGO = 250  # Dimensione standard del logo MyClipzo

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

# --- FUNZIONE TAGLIO VIDEO (FFMPEG) ---
def taglia_e_registra_clip(video_nome, inizio_sec, durata_sec, utente_email):
    """Taglia una clip dal video 4K senza perdere qualità"""
    
    input_p = os.path.join(VIDEO_DIR, video_nome) # Video originale (70 min)
    
    # Nome unico per la clip: MyClipzo_ORA_EMAIL.mp4
    timestamp_clip = datetime.now().strftime('%H%M%S')
    nome_output = f"MyClipzo_{timestamp_clip}.mp4"
    output_p = os.path.join(CLIP_GDRIVE, nome_output)

    # Comando FFmpeg ultra-veloce (-c copy)
    comando = [
        'ffmpeg', '-y',
        '-i', input_p,          # Prima carichiamo il video
        '-ss', str(inizio_sec), # Poi diciamo da dove iniziare
        '-t', str(durata_sec),  # Per quanto tempo
        '-c', 'copy',           # Copia senza sforzo
        output_p
    ]

    try:
        # Eseguiamo il taglio nel "sottobosco" del PC
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Salviamo l'evento del taglio su Supabase per lo storico dell'utente
        supabase.table("clip_generate").insert({
            "email_utente": utente_email,
            "nome_file": nome_output,
            "data_creazione": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }).execute()
        
        return output_p
    except Exception as e:
        st.error(f"Errore durante il taglio video: {e}")
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
    
    # 2. CREAZIONE COLONNE: 7 spazi se è Admin (ha il tasto segreto), 6 per gli altri
    # Usiamo col_nav per indicare le colonne della barra
    col_nav = st.columns(7 if is_admin else 6)
    
    # 3. PULSANTI DI NAVIGAZIONE (Usano la funzione vai_a del blocco precedente)
    with col_nav[0]: st.button("🏠 Home", on_click=lambda: vai_a('home_auth'), use_container_width=True)
    with col_nav[1]: st.button("👤 Profilo", on_click=lambda: vai_a('profilo'), use_container_width=True)
    with col_nav[2]: st.button("🏟️ Partite", on_click=lambda: vai_a('partite'), use_container_width=True)
    with col_nav[3]: st.button("🏆 Hall", on_click=lambda: vai_a('hall_of_fame'), use_container_width=True)
    with col_nav[4]: st.button("🎞️ Clip", on_click=lambda: vai_a('mie_clip'), use_container_width=True)
    
    # Tasto speciale per il Gestore del Centro (Admin)
    if is_admin:
        with col_nav[5]: st.button("🛡️ Admin", on_click=lambda: vai_a('admin'), use_container_width=True)
    
    # 4. TASTO LOGOUT (Sempre nell'ultima colonna a destra)
    with col_nav[-1]: 
        if st.button("🚪 Esci", type="secondary", use_container_width=True):
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
    # 1. LOGO CENTRATO (Gestione sicura: se non c'è il file, il sito non crasha)
    try:
        if os.path.exists("logo.png"):
            _, col_logo, _ = st.columns([1, 1.5, 1]) # Proporzioni centrate
            with col_logo:
                st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #28a745;'>MyClipzo</h1>", unsafe_allow_html=True)
    
    st.write(" ") # Spaziatura estetica

    # Visualizziamo i contenuti solo se l'utente non è loggato
    if not st.session_state.autenticato:
        st.markdown("<h2 style='text-align: center;'>Gioca. Rivediti. Condividi.</h2>", unsafe_allow_html=True)
        st.markdown("""
            <p style='text-align: center; font-size: 16px;'>
            Ogni partita merita di essere ricordata!<br>
            MyClipzo registra automaticamente le tue azioni e ti permette di creare highlight
            professionali</p>
        """, unsafe_allow_html=True)
        
        st.divider()

        # --- SEZIONE: COME FUNZIONA (LAYOUT A 3 COLONNE) ---
        st.markdown("<h2 style='text-align: center;'>Come Funziona</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.success("📹 **REGISTRAZIONE AUTOMATICA**")
            st.markdown("<p style='font-size: 14px; text-align: center;'>Il nostro sistema registra ogni partita in alta definizione 4k senza intervento manuale.</p>", unsafe_allow_html=True)
        
        with c2:
            st.success("🔍 **TAGLIO CLIP ISTANTANEO**")
            st.markdown("<p style='font-size: 14px; text-align: center;'>Seleziona il momento esatto e genera la tua clip personalizzata in pochi secondi.</p>", unsafe_allow_html=True)
        
        with c3:
            st.success("📥 **CONDIVISIONE SOCIAL**")
            st.markdown("<p style='font-size: 14px; text-align: center;'>Pubblica le tue azioni migliori nella Hall of Fame e tagga i tuoi amici sui social.</p>", unsafe_allow_html=True)
            
        st.write("<br>", unsafe_allow_html=True)

        # --- SEZIONE: NEWSLETTER (INTEGRAZIONE SUPABASE + EMAIL) ---
        st.markdown("<h3 style='text-align: center;'>Resta aggiornato</h3>", unsafe_allow_html=True)
        _, col_news, _ = st.columns([1, 2, 1])
        st.markdown("<p style='text-align: center; color: #888; font-size: 14px;'>Iscriviti alla newsletter per ricevere novità, offerte e aggiornamenti sul mondo MyClipzo.</p>", unsafe_allow_html=True)

        _, col_news, _ = st.columns([1, 2, 1])
        with col_news:
            # Usiamo un form per pulire i campi dopo l'invio
            with st.form("newsletter_form", clear_on_submit=True):
                email_input = st.text_input("La tua migliore Email", placeholder="esempio@mail.com").strip().lower()
                submit_news = st.form_submit_button("ISCRIVITI ALLA NEWSLETTER")
                
                if submit_news:
                    if "@" in email_input and "." in email_input:
                        # Funzione definita nel Blocco 3 (Salva su Supabase e invia Mail)
                        invio_ok = invia_conferma_e_salva(email_input)
                        if invio_ok:
                            st.success("✅ Benvenuto a bordo! Controlla la tua email.")
                        else:
                            st.info("ℹ️ Ti abbiamo registrato nel database, ma l'email di conferma arriverà a breve.")
                    else:
                        st.error("❌ Per favore, inserisci un indirizzo email valido.")

        # --- PULSANTE DI ACCESSO PRINCIPALE ---
        st.write("<br><br>", unsafe_allow_html=True)
        _, col_btn_home, _ = st.columns([1, 1, 1])
        with col_btn_home:
            # Reindirizza alla pagina di Login
            st.button("🚀 ACCEDI AL PORTALE", on_click=lambda: vai_a('login'), use_container_width=True)

       


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
            st.markdown("<h2 style='text-align: center;'>Accedi a MyClipzo</h2>", unsafe_allow_html=True)
            
            # Input utente
            u_login = st.text_input("Email", placeholder="la-tua@email.com").strip().lower()
            p_login = st.text_input("Password", type="password", placeholder="******")
            
            if st.button("ENTRA", use_container_width=True):
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
            
            

        # --- 2. SOTTO-PAGINA: REGISTRAZIONE ---
        elif st.session_state.sub == 'reg':
            st.markdown("<h2 style='text-align: center;'>Crea il tuo Account</h2>", unsafe_allow_html=True)
            
            r_n = st.text_input("Nome", placeholder="es. Mario")
            r_c = st.text_input("Cognome", placeholder="es. Rossi")
            r_e = st.text_input("Email", placeholder="mario.rossi@mail.com").strip().lower()
            r_p = st.text_input("Scegli una Password", type="password")
            
            if st.button("CONFERMA REGISTRAZIONE", use_container_width=True):
                if r_n and r_c and r_e and r_p:
                    try:
                        # Controlliamo prima se l'email esiste già (Uso della funzione creata nel Blocco 5)
                        nuovo_utente = {
                            "nome": r_n, 
                            "cognome": r_c, 
                            "email": r_e, 
                            "password": r_p, 
                            "ruolo": "Player"
                        }
                        supabase.table("utenti").insert(nuovo_utente).execute()
                        st.success("✅ Account creato con successo! Ora puoi accedere.")
                        st.session_state.sub = 'login'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: Email già registrata o problema tecnico.")
                else: 
                    st.error("⚠️ Inserisci tutti i dati richiesti!")
            
            if st.button("🔙 TORNA AL LOGIN", type="secondary", use_container_width=True): 
                st.session_state.sub = 'login'
                st.rerun()

        # --- 3. SOTTO-PAGINA: RECUPERO PASSWORD ---
        elif st.session_state.sub == 'recupero':
            st.markdown("<h2 style='text-align: center;'>Recupero Credenziali</h2>", unsafe_allow_html=True)
            m_rec = st.text_input("La tua Email di registrazione").strip().lower()
            
            if st.button("INVIA ISTRUZIONI", use_container_width=True):
                if m_rec:
                    st.info(f"Se l'account esiste, riceverai una mail a {m_rec} (Funzione in test)")
                else:
                    st.warning("Inserisci un'email!")
            
            if st.button("🔙 TORNA AL LOGIN", type="secondary", use_container_width=True): 
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

    # 2. ARCHIVIO CLIP TAGLIATE (Le azioni scelte dai ragazzi)
    st.markdown("#### ✂️ Clip Generate dagli Utenti")

    try:
        # Recuperiamo le clip estratte dagli utenti (stato 'CLIP_UTENTE')
        res_clips = supabase.table("calendario")\
            .select("id, data, campo, evento")\
            .eq("stato", "CLIP_UTENTE")\
            .order("id", desc=True)\
            .execute()

        if res_clips.data:
            df_clips_admin = pd.DataFrame(res_clips.data)
            
            # Rinominia per rendere la tabella comprensibile al gestore
            # (Nel tuo database 'campo' salva l'email e 'evento' il nome del file clip)
            df_visualizza = df_clips_admin.rename(columns={
                'id': 'ID Clip',
                'data': 'Data Taglio',
                'campo': 'Email Utente', 
                'evento': 'Nome File Clip'
            })
            
            st.dataframe(
                df_visualizza, 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ Nessun utente ha ancora generato delle clip personali.")

    except Exception as e:
        st.error(f"Errore caricamento tabella clip: {e}")

    st.divider()


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

        # 2. ARCHIVIO VIDEO E RICHIESTA CLIP (LOGICA ASINCRONA)
        st.markdown("### 🎞️ Archivio Match Registrati")
        
        try:
            # Recuperiamo le partite concluse (stato 'FATTO')
            res_matches = supabase.table("calendario")\
                .select("*")\
                .eq("stato", "FATTO")\
                .order("id", desc=True)\
                .execute()
            
            partite_fatte = res_matches.data

            if not partite_fatte:
                st.info("ℹ️ Nessuna partita registrata disponibile per il taglio.")
            else:
                for partita in partite_fatte:
                    st.subheader(f"🏟️ {partita['evento']} ({partita['data']})")
                    
                    video_url = make_direct_link(partita.get("link_video"))  # URL caricato dal Mini PC (GDrive/S3/Cloud)

                    if video_url:
                        # Anteprima video per trovare il momento del goal
                        st.video(video_url, format="video/mp4")
                        
                        # BOX TAGLIO CLIP
                        with st.expander("✂️ RICHIEDI TAGLIO CLIP DI UN'AZIONE"):
                            st.write("Inserisci il momento esatto dell'azione che vuoi salvare:")
                            
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                m_in = st.number_input("Minuto inizio", min_value=0, max_value=90, step=1, key=f"m_{partita['id']}")
                            with c2:
                                s_in = st.number_input("Secondo inizio", min_value=0, max_value=59, step=1, key=f"s_{partita['id']}")
                            with c3:
                                durata_clip = st.number_input("Durata (sec)", min_value=5, max_value=60, value=15, key=f"d_{partita['id']}")

                            if st.button("🎬 GENERA CLIP", key=f"btn_{partita['id']}", use_container_width=True):
                                # Calcolo del tempo totale in secondi per FFmpeg
                                inizio_totale_secondi = (m_in * 60) + s_in
                                
                                # Inviamo l'ordine di lavoro alla tabella 'comandi_clip'
                                # Il Mini PC in campo leggerà questa riga e taglierà il file originale 4K
                                try:
                                    supabase.table("comandi_clip").insert({
                                        "id_partita": partita['id'],
                                        "inizio_secondi": inizio_totale_secondi,
                                        "durata_secondi": durata_clip,
                                        "email_utente": st.session_state.user_email,
                                        "stato": "RICHIESTO"
                                    }).execute()
                                    
                                    st.success("✅ Richiesta inviata! Il Mini PC sta lavorando il video. La troverai tra poco in 'Le Mie Clip'.")
                                except Exception as e:
                                    st.error(f"Errore invio comando: {e}")
                    else:
                        st.warning("⚠️ Video Master in fase di caricamento sul Cloud...")
                    
                    st.divider()

        except Exception as e:
            st.error(f"Errore caricamento archivio: {e}")

# --- BLOCCO PROFILO: VERSIONE INTEGRALE E CORRETTA ---
elif st.session_state.pagina == 'profilo':
    st.markdown("<h2 style='text-align: center;'>👤 Area Personale MyClipzo</h2>", unsafe_allow_html=True)
    
    try:
        import time
        email_sessione = st.session_state.user_email.strip().lower()
        
        # 1. Recupero dati Utente (FIX: single record)
        res_u = supabase.table("utenti").select("*").eq("email", email_sessione).maybe_single().execute()
        user = res_u.data
        
        if user:
            # --- SEZIONE A: MODIFICA DATI ---
            with st.expander("⚙️ Modifica Dati e Carica Foto"):
                col_f, col_i = st.columns(2)
                with col_f:
                    st.write("📷 **La tua Foto**")
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

                if st.button("💾 SALVA TUTTE LE MODIFICHE", use_container_width=True, type="primary"):
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
                st.markdown(f'<div style="background:#262730; padding:10px; border-radius:10px; margin-bottom:5px;"><b>Nickname:</b> {user.get("nickname") or "N/A"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#262730; padding:10px; border-radius:10px; margin-bottom:5px;"><b>Instagram:</b> {user.get("ig_tag") or "N/A"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#262730; padding:10px; border-radius:10px; margin-bottom:5px;"><b>Ruolo:</b> {user.get("ruolo") or "Player"}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#262730; padding:10px; border-radius:10px; margin-bottom:5px;"><b>Email:</b> {email_sessione}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#262730; padding:10px; border-radius:10px;"><b>Bio:</b> {user.get("bio") or "Nessuna bio"}</div>', unsafe_allow_html=True)

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
            st.subheader("📊 Statistiche Personali")
            s_cols = st.columns(6)
            stats = [("🎞️","Clip", len(res_c.data)), ("⚽","Goal", "0"), ("👟","Assist", "0"), ("🏆","Rank", "-"), ("🏅","Badge", "0"), ("🔥","Azioni", "0")]
            for i, (ico, tit, val) in enumerate(stats):
                with s_cols[i]: 
                    st.markdown(f'<div style="text-align:center; background:#1E1E1E; padding:10px; border-radius:10px; border:1px solid #28a745;">{ico}<br><small>{tit}</small><br><b>{val}</b></div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("🏆 I tuoi badge")
            st.info("🏅 Partecipa a più partite per sbloccare i tuoi primi badge!")

        else: 
            st.error("⚠️ Utente non trovato nel database.")
            
    except Exception as e:
        st.error(f"Errore tecnico nel profilo: {e}")


# --- NUOVO BLOCCO: PAGINA PARTITE (VERSIONE AUTOMATICA CON AUTO-FIX LINK) ---
if st.session_state.pagina == 'partite':
    import re
    import streamlit.components.v1 as components
    
    st.title("🏟️ PARTITE DISPONIBILI")

    # Funzione interna per pulire i link (vecchi e nuovi)
    def pulisci_link_drive(link):
        if not link: return None
        # Se il link è già nel formato /preview, lo lasciamo così
        if "/preview" in link: return link
        # Se è un link standard, estraiamo l'ID e creiamo il formato /preview
        match = re.search(r"id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)", link)
        if match:
            video_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/file/d/{video_id}/preview"
        return link

    try:
        # 1. Prendiamo i match 'FATTO' dal calendario
        match_resp = supabase.table("calendario")\
            .select("*")\
            .eq("stato", "FATTO")\
            .order("id", desc=True)\
            .execute()

        match_list = match_resp.data or []

        if not match_list:
            st.info("📌 Nessuna partita terminata trovata nel calendario.")
        else:
            for partita in match_list:
                st.subheader(f"📅 Gara del {partita.get('data')} - Ore {partita.get('ora')}")

                # 2. Cerchiamo il video corrispondente nella tabella video
                nome_cercato = f"match_{partita['id']}_"
                video_resp = supabase.table("video")\
                    .select("*")\
                    .like("nome_file", f"%{nome_cercato}%")\
                    .limit(1).execute()

                video = video_resp.data[0] if video_resp.data else None

                if video and video.get("url_video"):
                    # TRUCCO: Puliamo il link "al volo" per attivare il player di Google
                    url_embed = pulisci_link_drive(video["url_video"])
                    
                    st.write(f"🎬 Video: {video['nome_file']}")
                    
                    # Carichiamo il player ufficiale con tutti i tasti (Play, Vol, Zoom)
                    components.iframe(url_embed, height=480, scrolling=False)
                    
                    st.caption("💡 Se il video è nero, assicurati che la cartella su Drive sia 'Pubblica' (Chiunque abbia il link).")
                else:
                    st.warning("⏳ Video in fase di caricamento o non trovato.")
                
                st.divider()

    except Exception as e:
        st.error(f"⚠️ Errore nel caricamento: {e}")





# --- NUOVO BLOCCO: PAGINA PARTITE (SOLUZIONE DEFINITIVA "OPEN EXTERNAL") ---
if st.session_state.pagina == 'partite':
    import re
    import streamlit.components.v1 as components
    
    #st.title("🏟️ Archivio Partite MyPlayr")

    def prepara_link_video(link_grezzo):
        if not link_grezzo: return None, None
        # Estraiamo l'ID del video
        match = re.search(r"id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)", link_grezzo)
        if match:
            video_id = match.group(1) or match.group(2)
            # Link per il riquadro interno (spesso bloccato dai cookie)
            url_embed = f"https://google.com{video_id}/preview?authuser=0"
            # Link per l'apertura esterna (FUNZIONA SEMPRE)
            url_esterno = f"https://google.com{video_id}/view"
            return url_embed, url_esterno
        return link_grezzo, link_grezzo

    try:
        res_cal = supabase.table("calendario").select("*").eq("stato", "FATTO").order("id", desc=True).execute()
        partite_concluse = res_cal.data if res_cal.data else []

        if not partite_concluse:
            st.info("📌 Nessuna partita terminata trovata.")
        else:
            for partita in partite_concluse:
                #st.subheader(f"📅 Gara del {partita.get('data')} - Ore {partita.get('ora')}")

                id_cercato = f"match_{partita['id']}_"
                res_vid = supabase.table("video").select("*").like("nome_file", f"%{id_cercato}%").limit(1).execute()
                video_data = res_vid.data[0] if res_vid.data else None

        if video_data and video_data.get("url_video"):
                    url_embed, url_esterno = prepara_link_video_completo(video_data["url_video"])
                    
                    # 1. DEFINIAMO LE COLONNE (2 parti al video, 1 al form)
                    col_v, col_f = st.columns([2, 1.2], gap="large")
                    
                    with col_v:
                        # Video a sinistra con altezza ridotta per non distorcere
                        # Usiamo 350-400 invece di 480 per evitare l'effetto "gigante"
                        components.iframe(url_embed, height=380, scrolling=False)
                        
                        # Info Partita (Box Bianco come nello screenshot)
                        st.markdown(f"""
                            <div style='background-color: white; padding: 12px; border: 1px solid #ddd; border-radius: 8px; margin-top: -10px;'>
                                <h4 style='margin:0; color: #333;'>🏟️ {partita.get('evento', 'Campo Centrale')}</h4>
                                <p style='font-size: 13px; color: #666; margin: 5px 0 0 0;'>
                                    📅 {partita.get('data')} | 🕒 Durata: 1:30:00 | ⏱️ Tempo: 0:00
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Tasto emergenza più piccolo sotto il box
                        st.link_button("▶️ Apri in nuova finestra (se nero)", url_esterno, use_container_width=True)

                    with col_f:
                        # 2. MODULO RICHIESTA A DESTRA (Stile FaceSoccer)
                        st.markdown("### Richiedi la tua clip")
                        
                        # Campi di input con etichette chiare
                        m_in = st.text_input("Minuto esatto (MM:SS) *", placeholder="es. 12:34", key=f"fs_m_{partita['id']}")
                        t_az = st.text_input("Tipo Azione *", placeholder="es. Goal, Parata", key=f"fs_a_{partita['id']}")
                        m_cl = st.text_input("Email ricezione *", value=st.session_state.get('user_email', ''), key=f"fs_e_{partita['id']}")
                        
                        st.write("") # Spazio tattico
                        
                        # Bottone Verde FaceSoccer
                        if st.button("Vai alla generazione", key=f"fs_btn_{partita['id']}", use_container_width=True):
                            if m_in and t_az and m_cl:
                                try:
                                    m_s, s_s = map(int, m_in.split(':'))
                                    in_tot = (m_s * 60) + s_s
                                    supabase.table("comandi_clip").insert({
                                        "id_partita": partita['id'], "inizio_secondi": in_tot, "durata_secondi": 20,
                                        "email_utente": m_cl, "stato": "RICHIESTO", "descrizione": t_az
                                    }).execute()
                                    st.success("✅ Richiesta inviata!")
                                except:
                                    st.error("❌ Formato MM:SS errato")
                            else:
                                st.warning("⚠️ Compila i campi")

                
                #st.divider()

    except Exception as e:
        st.error(f"⚠️ Errore: {e}")


# --- PAGINA PRIVACY POLICY ---
elif st.session_state.pagina == 'privacy':
    st.markdown("<h1 style='text-align: center; color: white;'>🛡️ Privacy Policy</h1>", unsafe_allow_html=True)
    
    # Incolla il tuo testo tra le triple virgolette
    testo_privacy = """ 1. Titolare del Trattamento
Il titolare è MyClipzo (email: privacy@myclipzo.com). Per i servizi presso i centri sportivi, MyClipzo agisce come Responsabile Esterno o Contitolare insieme alla Struttura Ospitante.

2. Tipologia di dati raccolti
Nome, cognome, email, username, dati tecnici di navigazione e contenuti video/immagini generati durante l'attività sportiva.
3. Finalità del trattamento
Registrazione, accesso all'area personale, generazione/download delle clip e condivisione volontaria sui social. I video sono trattati esclusivamente per scopi sportivi e ricreativi.
4. Base giuridica
Il trattamento avviene sulla base dell'esecuzione del contratto (erogazione servizio) e del consenso esplicito dell'utente.
5. Conservazione dei dati
I dati dell'account restano attivi fino a richiesta di cancellazione. I file video originali vengono conservati per un massimo di 60 giorni, dopodiché vengono eliminati definitivamente per ragioni di storage.
6. Condivisione dei dati
I dati non sono venduti a terzi. Sono accessibili solo ai partner tecnologici necessari (es. Cloud Storage, Database) vincolati al segreto professionale.
7. Diritti dell’utente
Accesso, rettifica, cancellazione (oblio) e revoca del consenso inviando una mail a: privacy@myclipzo.com.
8. Sicurezza
Adottiamo protocolli di crittografia e accesso sicuro (2FA) per proteggere i flussi video.

    """
    
    st.markdown(f"<div style='text-align: justify; color: white;'>{testo_privacy}</div>", unsafe_allow_html=True)

# --- PAGINA DIRITTI RISERVATI ---
elif st.session_state.pagina == 'diritti':
    st.markdown("<h2 style='text-align: center; color: white;'>© Diritti Riservati</h2>", unsafe_allow_html=True)
    
    testo_diritti = """
    Proprietà dei Contenuti e Diritti Riservati
Tutti i contenuti presenti su questo sito, inclusi testi, grafica, loghi, icone, immagini e il software di gestione, sono di proprietà esclusiva di MyClipzo o dei suoi licenzianti e sono protetti dalle leggi internazionali sul diritto d'autore.
Riprese Video e Clip:
Le riprese effettuate durante gli eventi sportivi hanno finalità di analisi tecnica e documentazione amatoriale. I diritti relativi alle immagini appartengono a MyClipzo, fermo restando il diritto all'immagine dei partecipanti.
Limitazioni d'uso:
È severamente vietata la riproduzione, la modifica, la distribuzione, la trasmissione o la pubblicazione dei video e delle clip presenti nel sito per scopi commerciali senza l'espressa autorizzazione scritta di MyClipzo. L'utente ha il diritto di visualizzare e scaricare le proprie clip esclusivamente per uso personale e privato (social network inclusi, previo tag della pagina ufficiale).
© 2026 MyClipzo - Tutti i diritti riservati.
    """
    
    st.markdown(f"<div style='color: white; text-align: justify;'>{testo_diritti}</div>", unsafe_allow_html=True)
    
    


# --- PAGINA TERMINI E CONDIZIONI ---
elif st.session_state.pagina == 'termini':
    st.markdown("<h1 style='text-align: center; color: white;'>⚖️ Termini e Condizioni</h1>", unsafe_allow_html=True)
    
    # Incolla il tuo testo tra le triple virgolette
    testo_termini = """
   

1. Descrizione del servizio
Piattaforma digitale per la fruizione di clip video generate in strutture partner. Il servizio è fornito "così com'è" per scopi di intrattenimento.

2. Registrazione
L'utente dichiara di avere almeno 18 anni o di possedere il consenso dei genitori.

3. Utilizzo delle clip
Le clip sono per uso personale. La condivisione sui social è una scelta libera e consapevole dell'utente.

4. Responsabilità dell’utente
È vietato l'uso delle clip per scopi diffamatori, illegali o per ledere la dignità altrui. L'utente è l'unico responsabile dei contenuti pubblicati.

5. Limitazione di responsabilità
MyClipzo non garantisce la continuità del servizio in caso di guasti tecnici o mancanza di rete nel centro sportivo. Le riprese non hanno valore legale o arbitrale e non possono essere usate in procedimenti disciplinari o civili.

6. Sospensione
Ci riserviamo di chiudere account che violano le regole di community o caricano contenuti impropri.

7. Foro competente
Per ogni controversia è competente il Foro di [Tua Città], Italia.

    """
    
    st.markdown(f"<div style='text-align: justify; color: white;'>{testo_termini}</div>", unsafe_allow_html=True)
    

# --- BLOCCO: PAGINA HALL OF FAME PRO (FIXED) ---

if st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>🏆 MyClipzo Hall of Fame</h1>", unsafe_allow_html=True)
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


# --- TASTO DI RITORNO SICURO (DA METTERE PRIMA DEL FOOTER) ---
# Usiamo una chiave diversa per non andare in conflitto con i tasti precedenti
if st.session_state.pagina not in ['home', 'home_auth']:
    if st.button("🔙 Torna alla Home", key="btn_ritorno_universale"):
        if st.session_state.get('autenticato', False):
            st.session_state.pagina = 'home_auth'
        else:
            st.session_state.pagina = 'home'
        st.rerun()


# --- BLOCCO FINALE: ALTRE PAGINE & FOOTER ---

# 1. GESTIONE PAGINE MINORI (Recupero Password)
if st.session_state.pagina == 'recupero_password': 
    st.markdown("<h2 style='text-align: center;'>Recupero Password</h2>", unsafe_allow_html=True)
    st.info("Abbiamo inviato le istruzioni alla tua email.")
    st.button("🔙 Torna al Login", on_click=lambda: vai_a('login'), use_container_width=True)

# --- 2. FOOTER UNIVERSALE (GRAFICA ORIGINALE + CLICK FUNZIONANTE) ---
st.markdown("""
    <style>
    /* Rende i bottoni del footer identici a scritte semplici bianche */
    div.stButton > button[kind="secondary"] {
        border: none !important;
        background: transparent !important;
        color: white !important;
        padding: 0 !important;
        margin: 0 !important;
        font-weight: normal !important;
        text-align: left !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        color: #cccccc !important; /* Diventa grigio chiaro al passaggio del mouse */
        text-decoration: underline !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold;'>MyClipzo - Video Analysis Pro</p>", unsafe_allow_html=True)

f_l, f_r = st.columns(2)

with f_l: 
    # Pulsante camuffato da scritta bianca
    if st.button("📄 Privacy Policy", key="footer_privacy_link"):
        st.session_state.pagina = 'privacy'
        st.rerun()

with f_r: 
    # Allineamento a destra simulato con una colonna o spazi (Streamlit centra i bottoni di default)
    if st.button("⚖️ Termini e Condizioni", key="footer_termini_link"):
        st.session_state.pagina = 'termini'
        st.rerun()


# --- COPYRIGHT CLICCABILE NEL FOOTER ---
st.markdown("<br>", unsafe_allow_html=True) # Un po' di spazio

if st.button(f"© 2026 MyClipzo - Tutti i diritti riservati", key="f_copy_btn", use_container_width=True):
    st.session_state.pagina = 'diritti'
    st.rerun()

# CSS per far sembrare il bottone una semplice scritta bianca
st.markdown("""
    <style>
    button.st-key-f_copy_btn {
        border: none !important;
        background: transparent !important;
        color: white !important;
        font-size: 13px !important;
        margin-top: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)


