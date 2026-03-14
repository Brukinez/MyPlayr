import streamlit as st
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import smtplib
from email.mime.text import MIMEText
import os
from supabase import create_client
from dotenv import load_dotenv

# Carichiamo le chiavi dal file .env (che hai già creato)
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# --- REGOLAZIONE LOGO (Cambia questo numero per la grandezza) ---
GRANDEZZA_LOGO = 250  # <--- Prova 350, se è troppo grande metti 300 o 250

# test

def taglia_e_registra_clip(video_nome, inizio_sec, durata_sec, utente_email):
    import subprocess
    input_p = os.path.join(VIDEO_DIR, video_nome) # Legge dal PC
    nome_output = f"MyPlayr_{datetime.now().strftime('%H%M%S')}.mp4"
    output_p = os.path.join(CLIP_GDRIVE, nome_output) # Salva su G:
    
    # Comando ultra-leggero (Stream Copy)
    comando = ['ffmpeg', '-y', '-ss', str(inizio_sec), '-t', str(durata_sec), 
               '-i', input_p, '-c', 'copy', output_p]
    
    
    try:
        subprocess.run(comando, check=True)
        # Registriamo comunque nel database per il tuo archivio Admin
                # --- NUOVO SALVATAGGIO CLIP SU SUPABASE ---
        nuova_clip = {
            "data": datetime.now().strftime("%d-%m-%Y"),
            "ora": "CLIP",
            "campo": utente_email,    # Usiamo il campo per identificare l'utente
            "evento": nome_output,   # Nome del file video tagliato
            "stato": "CLIP_UTENTE"
        }
        
        try:
            from database import supabase
            supabase.table("calendario").insert(nuova_clip).execute()
            print(f"✅ Clip '{nome_output}' registrata nel Cloud per {utente_email}")
        except Exception as e:
            print(f"❌ Errore salvataggio clip Cloud: {e}")

        return output_p # Restituiamo il percorso completo del file su G:
    except:
        return None

# Percorso per salvare le clip su Google Drive (Disco G:)
CLIP_GDRIVE = r"G:\Il mio Drive\CLIP_MYPLAYR"
if not os.path.exists(CLIP_GDRIVE): os.makedirs(CLIP_GDRIVE)



# --- FUNZIONE NEWSLETTER ---
def invia_conferma_e_salva(email_utente):
    # Salvataggio nel file iscritti.txt
    with open(os.path.join(BASE_DIR, "iscritti.txt"), "a") as file:
        file.write(f"{email_utente} - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Configurazione Email (Sostituisci i dati qui sotto!)
    mio_indirizzo = "simone.fardella@gmail.com"  
    mia_password = "xinqcxwubwuasurc"   
    
    msg = MIMEText(f"Grazie per esserti iscritto alla newsletter di Myplayr!")
    msg['Subject'] = "Conferma Iscrizione Myplayr"
    msg['From'] = mio_indirizzo
    msg['To'] = email_utente

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mio_indirizzo, mia_password)
            server.sendmail(mio_indirizzo, email_utente, msg.as_string())
        return True
    except:
        return False

# --- CONFIGURAZIONE PERCORSI ---import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")
DB_PATH = os.path.join(BASE_DIR, "myplayr_finale.db")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# --- FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabelle base
    c.execute('''CREATE TABLE IF NOT EXISTS calendario (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora TEXT, campo TEXT, evento TEXT, stato TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS utenti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cognome TEXT, nickname TEXT, email TEXT UNIQUE, password TEXT, ruolo TEXT, bio TEXT, data_iscrizione TEXT, foto_path TEXT, ig_tag TEXT)''')
    
    # --- CONTROLLO COLONNA MANCANTE IN CALENDARIO ---
    c.execute("PRAGMA table_info(calendario)")
    cols_cal = [info[1] for info in c.fetchall()]
    if 'consenso_social' not in cols_cal:
        c.execute("ALTER TABLE calendario ADD COLUMN consenso_social INTEGER DEFAULT 0")
    
    conn.commit()
    try:
        c.execute("ALTER TABLE calendario ADD COLUMN link_video TEXT")
        conn.commit()
    except:
        pass # La colonna esiste già, non fare nulla
   
    conn.close()

# Eseguiamo subito la funzione per aggiornare il file .db
init_db()



init_db()
# Funzione rapida per aggiungere la colonna Instagram se manca
def aggiungi_colonna_social():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(utenti)")
    colonne = [info[1] for info in c.fetchall()]
    if 'ig_tag' not in colonne:
        c.execute("ALTER TABLE utenti ADD COLUMN ig_tag TEXT")
    conn.commit()
    conn.close()

aggiungi_colonna_social()

# --- STILE E CSS ---
st.set_page_config(page_title="MyPlayr", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #2F353B; color: white; }
    h1, h2, h3, p, span, label { color: white !important; }
    
    /* Pulsanti VERDI Principali */
    .stButton>button { 
        background-color: #28a745 !important; 
        color: white !important; 
        border: none !important; 
        font-weight: bold !important; 
        width: 100%; 
        padding: 12px; 
        border-radius: 5px; 
        text-transform: uppercase;
        font-size: 16px;
    }
    
    hr { border: 1px solid #28a745 !important; opacity: 1; }
    
    /* Avatar Profilo */
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .avatar-img { 
        width: 120px; height: 120px; 
        border-radius: 50%; 
        border: 4px solid #28a745; 
        object-fit: cover; 
        margin: 0 auto; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        background: #3E444A;
        font-size: 60px; /* Icona più grande */
    }
    
    .data-card { background-color: #3E444A; padding: 12px; border-radius: 8px; border-left: 5px solid #28a745; margin-bottom: 8px; font-size: 14px; }
    .stat-box { text-align: center; background: #3E444A; padding: 10px; border-radius: 8px; border: 1px solid #28a745; }

    /* Link Piccoli Navigazione */
    div[data-testid="stButton"] > button[kind="secondary"] { 
        background-color: transparent !important; 
        color: #d1d1d1 !important; 
        border: none !important; 
        font-size: 12px !important; 
        width: 100% !important; 
        text-transform: none !important; 
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { color: #28a745 !important; text-decoration: underline !important; }
    
    /* File Uploader Custom Label */
    .stFileUploader label { font-weight: bold !important; color: #28a745 !important; font-size: 16px !important; }

    .footer-main { text-align: center; font-size: 16px; margin-top: 50px; }
    .footer-sub { font-size: 12px; color: #888; }
    </style>
""", unsafe_allow_html=True)
# --- PROTEZIONE SITO (PASSWORD SVILUPPATORE) ---
if "password_dev_corretta" not in st.session_state:
    st.session_state["password_dev_corretta"] = False

if not st.session_state["password_dev_corretta"]:
    st.markdown("<h1 style='text-align: center;'>🚧 MyPlayr - Area Protetta</h1>", unsafe_allow_html=True)
    st.write("Il sito è attualmente in fase di sviluppo. Inserisci la password per visualizzare l'anteprima.")
    
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        pwd_inserita = st.text_input("Password Sviluppatore", type="password", placeholder="Scrivi qui...")
    with col_p2:
        st.write("<br>", unsafe_allow_html=True) # Spazio per allineare il tasto
        if st.button("SBLOCCA SITO"):
            if pwd_inserita == "myplayr2026": # <--- CAMBIA QUI LA TUA PASSWORD
                st.session_state["password_dev_corretta"] = True
                st.rerun()
            else:
                st.error("Password errata!")
    st.stop() # Questo comando blocca tutto il resto del sito se la password è sbagliata

# --- LOGICA NAVIGAZIONE ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
if 'autenticato' not in st.session_state: st.session_state.autenticato = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'editing' not in st.session_state: st.session_state.editing = False

def vai_a(nome):
    st.session_state.pagina = nome
    st.rerun()

# --- NAVBAR ---
if st.session_state.autenticato:
    is_admin = st.session_state.user_email == "admin@myplayr.com"
    nav_cols = st.columns(7 if is_admin else 6)
    with nav_cols[0]: st.button("🏠 Home", on_click=lambda: vai_a('home_auth'))
    with nav_cols[1]: st.button("👤 Profilo", on_click=lambda: vai_a('profilo'))
    with nav_cols[2]: st.button("🏟️ Partite", on_click=lambda: vai_a('partite'))
    with nav_cols[3]: st.button("🏆 Hall of Fame", on_click=lambda: vai_a('hall_of_fame'))

    with nav_cols[4]: st.button("🎞️ Le Mie Clip", on_click=lambda: vai_a('mie_clip'))
    if is_admin:
        with nav_cols[5]: st.button("🛡️ Admin", on_click=lambda: vai_a('admin'))
    with nav_cols[-1]: 
        if st.button("🚪 Logout", type="primary"):
            st.session_state.autenticato = False
            vai_a('home')
    st.divider()
# --- PAGINA: HALL OF FAME (PUBBLICA) ---
elif st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>🏆 MyPlayr Hall of Fame</h1>", unsafe_allow_html=True)
    st.write("---")

    conn = sqlite3.connect(DB_PATH)
    # Prendiamo TUTTE le clip utente senza filtri per testare la connessione
    df_fame = pd.read_sql("SELECT * FROM calendario WHERE stato='CLIP_UTENTE'", conn)
    conn.close()

    # --- SPIE DI CONTROLLO (DEBUG) ---
    st.info(f"📊 Clip totali nel sistema: {len(df_fame)}")
    
    # Filtriamo quelle con il consenso (1)
    clip_visibili = df_fame[df_fame['consenso_social'] == 1]
    st.success(f"✅ Clip con consenso attivo: {len(clip_visibili)}")

    if not clip_visibili.empty:
        for i, clip in clip_visibili.iterrows():
            path_fame = os.path.join(CLIP_GDRIVE, clip['evento'])
            
            with st.container():
                if os.path.exists(path_fame):
                    st.video(path_fame)
                    st.write(f"⚽ Azione di: **{clip['campo']}**")
                else:
                    st.warning(f"⚠️ File {clip['evento']} non trovato su Drive G:")
                st.divider()
    else:
        st.warning("La Hall of Fame è vuota. Assicurati di aver attivato 'Sì, pubblicami' in Le Mie Clip.")


# --- PAGINA 1: HOME PAGE (INTEGRALE) ---
elif st.session_state.pagina == 'home':
    # 1. LOGO XL PERFETTAMENTE CENTRATO
    if os.path.exists("logo.png"):
        # Creiamo 3 colonne: le due laterali spingono quella centrale
        col_vuota_1, col_logo_centrale, col_vuota_2 = st.columns([1, 2, 1])
        with col_logo_centrale:
            st.image("logo.png", use_container_width=True) # Si adatta alla colonna centrale

    
    
    # 3. SPAZIATURA
    st.write(" ") 


    
   


if st.session_state.pagina == 'home' and not st.session_state.autenticato:
    
    st.markdown("<h2 style='text-align: center;'>Gioca. Rivediti. Condividi.</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>Ogni partita merita di essere ricordata!<br>Il calcio amatoriale come quello vero.<br>Condividi le tue giornate con amici, famiglia e sui social media.</p>", unsafe_allow_html=True)
    
    
    st.markdown("<h2 style='text-align: center;'>Come Funziona</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px;'>Tre semplici passaggi per rivivere le tue migliori giocate:</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success("📹 **Giochi la Partita**")
        st.markdown("<p class='small-font' style='font-size: 14px !important;'>Scendi in campo e gioca la partita. Ogni goal viene registrato in alta qualità.</p>", unsafe_allow_html=True)
    with c2:
        st.success("🔍 **Trovi il Video**")
        st.markdown("<p class='small-font' style='font-size: 14px !important;'>Accedi alla piattaforma e trova facilmente i video delle tue partite organizzate per data.</p>", unsafe_allow_html=True)
    with c3:
        st.success("📥 **Scarichi la tua Clip**")
        st.markdown("<p class='small-font' style='font-size: 14px !important;'>Seleziona i tuoi momenti migliori e scarica le clip personalizzate da condividere.</p>", unsafe_allow_html=True)
        
    
    st.markdown("<h3 style='text-align: center;'>Resta in contatto</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Iscriviti per ricevere aggiornamenti e novità</p>", unsafe_allow_html=True)
    
    _, col_news, _ = st.columns(3)
    with col_news:
        with st.form("newsletter_form", clear_on_submit=True):
            email_input = st.text_input("La tua mail", placeholder="esempio@mail.com")
            submit_button = st.form_submit_button("INVIA")
            
            if submit_button:
                if "@" in email_input and "." in email_input:
                    successo = invia_conferma_e_salva(email_input)
                    if successo:
                        st.success("Iscrizione avvenuta! Controlla la tua email.")
                    else:
                        st.warning("Iscritto! (Problema con l'invio email)")
                else:
                    st.error("Inserisci un'email valida.")

   
    _, col_btn, _ = st.columns(3)
    with col_btn:
        st.button("🚀 ACCEDI AL PORTALE", on_click=lambda: vai_a('login'))

# --- LOGIN ---
elif st.session_state.pagina == 'login':
    _, col_log, _ = st.columns(3)
    with col_log:
        # Inizializzazione stato (se non esiste)
        if 'sub' not in st.session_state: 
            st.session_state.sub = 'login'

        # --- 1. MOSTRA SOLO ACCEDI ---
        if st.session_state.sub == 'login':
            st.markdown("<h2 style='text-align: center;'>Accedi</h2>", unsafe_allow_html=True)
            # Invece di: u = st.text_input("Email")
            u = st.text_input("Email").strip().lower() # .lower() mette tutto in minuscolo

            p = st.text_input("Password", type="password")
            
            if st.button("ENTRA"):
                conn = sqlite3.connect(DB_PATH)
                user = conn.execute("SELECT * FROM utenti WHERE email=? AND password=?", (u, p)).fetchone()
                conn.close()
                if (u == "admin@myplayr.com" and p == "admin123") or user:
                    st.session_state.autenticato = True; st.session_state.user_email = u
                    vai_a('profilo')
                else: st.error("Credenziali errate!")
            
            # Pulsanti di scambio (Rimuovono il modulo sopra e mostrano quello nuovo)
            if st.button("password dimenticata?", type="secondary"): 
                st.session_state.sub = 'recupero'; st.rerun()
            if st.button("Non hai ancora un account? Registrati", type="secondary"):
                st.session_state.sub = 'reg'; st.rerun()
            st.button("🔙 INDIETRO", on_click=lambda: vai_a('home'))

        # --- 2. MOSTRA SOLO REGISTRAZIONE (Sostituisce il Login) ---
        elif st.session_state.sub == 'reg':
            st.markdown("<h2 style='text-align: center;'>Registrati</h2>", unsafe_allow_html=True)
            r_n = st.text_input("Nome")
            r_c = st.text_input("Cognome")
            r_e = st.text_input("Email")
            r_p = st.text_input("Password", type="password")
            
        if st.button("CONFERMA REGISTRAZIONE"):
            if r_n and r_c and r_e and r_p:
                # --- NUOVA REGISTRAZIONE SU SUPABASE ---
                nuovo_utente = {
                    "nome": r_n,
                    "cognome": r_c,
                    "email": r_e.strip().lower(), # Pulizia email (fondamentale!)
                    "password": r_p,               # In futuro useremo l'hash
                    "ruolo": "Player"
                }
                
                try:
                    # Inserimento nel database online
                    supabase.table("utenti").insert(nuovo_utente).execute()
                    st.success("✅ Account creato con successo nel Cloud!")
                    st.balloons()
                    st.session_state.sub = 'login'
                    st.rerun()
                except Exception as e:
                    # Se l'email esiste già, Supabase darà errore (giustamente)
                    st.error(f"❌ Errore: L'email potrebbe essere già registrata. ({e})")
            else: 
                st.error("Riempi tutti i campi")


        # --- 3. MOSTRA SOLO RECUPERO (Sostituisce il Login) ---
        elif st.session_state.sub == 'recupero':
            st.markdown("<h2 style='text-align: center;'>Recupero</h2>", unsafe_allow_html=True)
            m_rec = st.text_input("Inserisci la tua Email")
            if st.button("INVIA PASSWORD"):
                st.info("Email inviata (funzione in test)")
            if st.button("🔙 TORNA AL LOGIN", type="secondary"): 
                st.session_state.sub = 'login'; st.rerun()


# --- PAGINA ADMIN (DASHBOARD COMPLETA) ---
elif st.session_state.pagina == 'admin':
    # 1. Recupero dati reali per i contatori
    conn = sqlite3.connect(DB_PATH)
    num_utenti = conn.execute("SELECT count(*) FROM utenti").fetchone()[0]
    num_partite = conn.execute("SELECT count(*) FROM calendario").fetchone()[0]
    conn.close()
    
    num_newsletter = 0
    if os.path.exists(os.path.join(BASE_DIR, "iscritti.txt")):
        with open(os.path.join(BASE_DIR, "iscritti.txt"), "r") as f:
            num_newsletter = len(f.readlines())

    st.title("📊 Dashboard Amministratore")

    # 2. Riga dei contatori (Cards)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("⚽ Partite", num_partite)
    with c2: st.metric("🎞️ Clip Visitate", "0")
    with c3: st.metric("💰 Ricavi", "€0.00")
    with c4: st.metric("👥 Giocatori", num_utenti)
    with c5: st.metric("📧 Newsletter", num_newsletter)
    with c6: st.metric("📈 Conv. Rate", "0.0%")

    st.divider()

    # 3. Grafico (50%) e Azioni Rapide
    col_graf, col_act = st.columns(2)
    with col_graf:
        st.subheader("📈 Ricavi (7gg)")
        dati_grafico = pd.DataFrame({"G": ["L", "M", "M", "G", "V", "S", "D"], "€": [10, 45, 30, 80, 60, 120, 90]})
        st.line_chart(dati_grafico, x="G", y="€", color="#28a745")
    with col_act:
        st.subheader("⚡ Tipologia Per Azioni")
        ca, cb = st.columns(2)
        with ca:
            st.button("📧 Newsletter", use_container_width=True)
            st.button("📂 Backup DB", use_container_width=True)
        with cb:
            st.button("🧹 Cache", use_container_width=True)
            st.button("📊 CSV", use_container_width=True)

    st.divider()

    # 4. Top 5 e Richieste Clip
    col_top, col_req = st.columns(2)
    with col_top:
        st.subheader("🏆 Top 5 Giocatori")
        st.table(pd.DataFrame({"USER": ["Bomber9", "Alex_G", "Simo_F", "Luca_S", "Pippo_I"], "TOT": ["€120", "€85", "€70", "€55", "€40"]}))
    with col_req:
        st.subheader("📩 Richieste Recenti")
        st.info("Richiesta: Alex_Goal (03/03)")
        st.info("Richiesta: Bomber99 (04/03)")

    st.divider()
    # --- 5. VISUALIZZAZIONE VIDEO REGISTRATI (Admin) ---
    st.subheader("🎞️ Archivio Registrazioni Completate")
    
    conn = sqlite3.connect(DB_PATH)
    # Recuperiamo solo le clip che il Regista ha segnato come 'FATTO'
    query = "SELECT id, data, campo, ora, evento FROM calendario WHERE stato = 'FATTO' ORDER BY id DESC"
    df_partite = pd.read_sql_query(query, conn)
    conn.close()

    if not df_partite.empty:
        for idx, row in df_partite.iterrows():
            with st.container():
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.write(f"📅 **{row['data']}** | 🏟️ {row['campo']} | 🕒 {row['ora']}")
                    st.write(f"📄 File: `{row['evento']}`")
                with col_del:
                    if st.button("🗑️", key=f"del_adm_{row['id']}"):
                        # Elimina file fisico e riga database
                        p_vid = os.path.join(VIDEO_DIR, row['evento'])
                        if os.path.exists(p_vid): os.remove(p_vid)
                        conn = sqlite3.connect(DB_PATH); conn.execute("DELETE FROM calendario WHERE id=?", (row['id'],)); conn.commit(); conn.close()
                        st.rerun()
                st.divider()
    else:
        st.info("Nessun video ancora registrato dal Regista.")

    # --- PROGRAMMAZIONE REGISTRAZIONE (Solo per Admin) ---
    st.divider()
    with st.expander("📅 PROGRAMMA NUOVA REGISTRAZIONE", expanded=False):
        with st.form("form_admin_reg"):
            d_reg = st.date_input("Giorno Gara", datetime.now())
            f_ora = st.text_input("Ora Inizio (es: 19:30)")
            f_titolo = st.text_input("Titolo Partita (Squadre)")
            if st.form_submit_button("CONFERMA PROGRAMMAZIONE"):
                nuovo_match = {
        "data": d_reg.strftime('%d-%m-%Y'),
        "ora": f_ora.strip().replace(" ", ""),
        "campo": "USB2.0 VGA UVC WebCam",
        "evento": f_titolo,
        "stato": "PROGRAMMATO"
    }
    supabase.table("calendario").insert(nuovo_match).execute()
    st.success("✅ Gara programmata nel Cloud!"); st.rerun()



    st.divider()

        # 6. Archivio Video Totale (Corretto)
    st.subheader("🎞️ Archivio Video Totale")
    conn = sqlite3.connect(DB_PATH)
        # 1. Tabella delle PARTITE INTERE (stato 'FATTO')
    st.markdown("### 🏟️ Archivio Partite Registrate")
    df_vids = pd.read_sql_query("SELECT id, data, ora, campo, evento FROM calendario WHERE stato='FATTO' ORDER BY id DESC", conn)
    
    if not df_vids.empty:
        st.dataframe(df_vids, use_container_width=True)
    else:
        st.info("Nessuna partita intera registrata al momento.")

    # 2. Tabella delle CLIP TAGLIATE (stato 'CLIP_UTENTE')
    st.markdown("### ✂️ Archivio Clip Tagliate dagli Utenti")
    df_clips_admin = pd.read_sql_query("SELECT id, data, campo as utente, evento as nome_clip FROM calendario WHERE stato='CLIP_UTENTE' ORDER BY id DESC", conn)
    
    if not df_clips_admin.empty:
        st.dataframe(df_clips_admin, use_container_width=True)
    else:
        st.info("Nessun utente ha ancora tagliato delle clip.")

    conn.close()


    if not df_vids.empty:
        for idx, row in df_vids.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1.5, 2, 1.5, 3.5, 1])
            c1.write(row['data'])
            c2.write("Campo A")
            c3.write(row['ora'])
            c4.write(row['evento'] if row['evento'] else "In elaborazione...")
            
            if c5.button("🗑️", key=f"del_g_{row['id']}"):
                nome_video = row['evento']
                if nome_video:
                    v_path = os.path.join(VIDEO_DIR, nome_video)
                    if os.path.exists(v_path):
                        os.remove(v_path)
                
                with sqlite3.connect(DB_PATH) as c:
                    c.execute("DELETE FROM calendario WHERE id=?", (row['id'],))
                st.rerun()
    else:
        st.info("Nessun video registrato in archivio.")

    st.divider()



    # 7. Bottone Indietro
    if st.button("🔙 Torna alla Home", key="back_adm"):
        vai_a('home_auth')

# --- FINE SEZIONE ADMIN E INIZIO SEZIONE PARTITE ---

# --- PAGINA PARTITE (PROGRAMMAZIONE + ARCHIVIO) ---
elif st.session_state.pagina == "Pannello Admin":
    st.title("⚙️ Controllo MyPlayr (Riservato)")
    with st.form("programma_match"):
        data_p = st.date_input("Data", key="admin_data")
        ora_p = st.text_input("Ora (es. 15:30)", key="admin_ora")
        campo_p = st.text_input("Campo", key="admin_campo")
        # --- NUOVO CODICE ADMIN (Supabase) ---
if st.form_submit_button("🔴 PROGRAMMA MATCH"):
    nuovo_match = {
        "data": data_p.strftime("%d-%m-%Y"),
        "ora": ora_p.replace(" ", ""), # Pulizia spazi come abbiamo imparato!
        "campo": campo_p,
        "stato": "PROGRAMMATO"
    }
    supabase.table("calendario").insert(nuovo_match).execute()
    st.success(f"✅ Match inviato al Cloud per le {ora_p}!")




    st.divider()

    # 2. VISUALIZZAZIONE PARTITE REGISTRATE E TAGLIO CLIP
    st.markdown("### 🎞️ Partite Disponibili")
    conn = sqlite3.connect(DB_PATH)
    # Filtriamo per stato 'FATTO' per mostrare solo i video pronti
    df_partite = pd.read_sql("SELECT * FROM calendario WHERE stato='FATTO' ORDER BY id DESC", conn)
    conn.close()

    if df_partite.empty:
        st.info("Nessuna partita registrata trovata nel database.")
    else:
        for index, row in df_partite.iterrows():
            st.subheader(f"Partita: {row['data']} - {row['ora']} ({row['campo']})")
            
            video_nome = str(row['evento']) if row['evento'] else ""
            percorso_g = os.path.join(r"G:\Il mio Drive\CLIP_MYPLAYR", video_nome)

            if os.path.exists(percorso_g) and video_nome != "":
                st.video(percorso_g)
                
                # Box per il taglio della clip
                with st.expander("✂️ CREA LA TUA CLIP PERSONALIZZATA"):
                    st.write("Scegli il momento dell'azione:")
                    c1, col_s, c3 = st.columns(3)
                    with c1:
                        m_in = st.number_input("Minuto inizio", min_value=0, step=1, key=f"min_{row['id']}")
                    with col_s:
                        s_in = st.number_input("Secondo inizio", min_value=0, max_value=59, step=1, key=f"sec_{row['id']}")
                    with c3:
                        durata_clip = st.number_input("Durata (sec)", min_value=1, max_value=60, value=10, key=f"dur_{row['id']}")

                    if st.button("🎬 GENERA E SCARICA CLIP", width='stretch', type='primary'):
                        inizio_tot = (m_in * 60) + s_in
                        
                        # Chiamata alla funzione tecnica
                        with st.spinner("Generazione clip in corso..."):
                            percorso_g = taglia_e_registra_clip(video_nome, inizio_tot, durata_clip, st.session_state.user_email)
                        
                        if percorso_g and os.path.exists(percorso_g):
                            st.success("✅ Clip generata correttamente!")
                            with open(percorso_g, "rb") as f:
                                st.download_button(
                                    label="📥 SCARICA ORA LA TUA CLIP",
                                    data=f,
                                    file_name=os.path.basename(percorso_g),
                                    mime="video/mp4",
                                    key=f"dl_btn_{row['id']}"
                                )
                        else:
                            st.error("Errore: Verifica la connessione al disco G: o FFmpeg.")
            else:
                st.warning(f"File video '{video_nome}' non ancora disponibile.")
            
            st.divider()

# --- PAGINA PARTITE DISPONIBILI (VISIBILE A TUTTI GLI UTENTI) ---
elif st.session_state.pagina == 'partite':
    st.title("🏟️ Archivio Partite MyPlayr")
    
    conn = sqlite3.connect(DB_PATH)
    # Prendiamo tutte le partite dal database
    df_partite = pd.read_sql("SELECT * FROM calendario WHERE stato='FATTO' ORDER BY id DESC", conn)
    conn.close()

    if df_partite.empty:
        st.info("Nessuna partita trovata nel database.")
    else:
        for index, row in df_partite.iterrows():
            st.subheader(f"Partita: {row['data']} - {row['ora']}")
            
            # Definiamo il video da cercare
            video_nome = str(row['evento']) if row['evento'] else ""
            video_path = os.path.join(VIDEO_DIR, video_nome)

            if os.path.exists(video_path) and video_nome != "":
                # 1. Mostriamo il video
                st.video(video_path)
                
                # 2. Box per il taglio della clip (Tutto allineato correttamente)
                with st.expander("✂️ CREA LA TUA CLIP PERSONALIZZATA"):
                    st.write("Scegli il momento dell'azione:")
                    c1, col_s, c3 = st.columns(3)
                    with c1:
                        m_in = st.number_input("Minuto inizio", min_value=0, step=1, key=f"min_{row['id']}")
                    with col_s:
                        s_in = st.number_input("Secondo inizio", min_value=0, max_value=59, step=1, key=f"sec_{row['id']}")
                    with c3:
                        durata_clip = st.number_input("Durata (sec)", min_value=1, max_value=60, value=10, key=f"dur_{row['id']}")

                    if st.button("🎬 GENERA E SCARICA CLIP", key=f"btn_pay_{row['id']}", use_container_width=True):
                        inizio_tot = (m_in * 60) + s_in
                        # Chiamiamo la funzione tecnica che salva su G:
                        percorso_g = taglia_e_registra_clip(video_nome, inizio_tot, durata_clip, st.session_state.user_email)
                        
                        if percorso_g and os.path.exists(percorso_g):
                            st.success("✅ Clip generata su Google Drive!")
                            with open(percorso_g, "rb") as f:
                                st.download_button(
                                    label="📥 SCARICA ORA LA TUA CLIP",
                                    data=f,
                                    file_name=os.path.basename(percorso_g),
                                    mime="video/mp4",
                                    key=f"dl_btn_{row['id']}"
                                )
                        else:
                            st.error("Errore: Verifica la connessione al disco G: o FFmpeg.")
            else:
                st.warning(f"File video '{video_nome}' non trovato in {VIDEO_DIR}")
            
            st.divider()

# --- PAGINA: LE MIE CLIP (VISIBILE ALL'UTENTE) ---
elif st.session_state.pagina == 'mie_clip':
    st.markdown("<h2 style='text-align: center;'>🎞️ I Tuoi Highlight</h2>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM calendario WHERE stato='CLIP_UTENTE' AND campo=? ORDER BY id DESC"
    mie_clip = pd.read_sql(query, conn, params=(st.session_state.user_email,))
    conn.close()

    if not mie_clip.empty:
        for index, row_c in mie_clip.iterrows():
            percorso_clip = os.path.join(CLIP_GDRIVE, row_c['evento'])
            with st.container():
                if os.path.exists(percorso_clip):
                    st.video(percorso_clip)
                    c1, c2 = st.columns(2)
                    with c1:
                        with open(percorso_clip, "rb") as f:
                            st.download_button("📥 SCARICA CLIP", f, file_name=row_c['evento'], key=f"dl_{row_c['id']}")
                    with c2:
                        stato_db = True if row_c.get('consenso_social', 0) == 1 else False
                        consenso = st.toggle("Sì, pubblicami su @MyPlayr", value=stato_db, key=f"tog_{row_c['id']}")
                        if consenso != stato_db:
                            nuovo_valore = 1 if consenso else 0
                            with sqlite3.connect(DB_PATH) as conn_up:
                                conn_up.execute("UPDATE calendario SET consenso_social=? WHERE id=?", (nuovo_valore, row_c['id']))
                            st.toast("Impostazioni social aggiornate!")
                    if stato_db:
                        st.success("✨ Visibile nella Hall of Fame!")
                else:
                    st.warning(f"Clip '{row_c['evento']}' in caricamento...")
                st.divider()
    else:
        st.info("Non hai ancora creato nessuna clip.")



# --- PAGINA: HALL OF FAME (PUBBLICA) ---
elif st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>🏆 MyPlayr Hall of Fame</h1>", unsafe_allow_html=True)
    st.divider()

    conn = sqlite3.connect(DB_PATH)
    # Cerchiamo i video e i nomi dei giocatori
    query_fame = """
        SELECT DISTINCT c.evento, c.campo, u.nickname, u.ig_tag 
        FROM calendario c
        LEFT JOIN utenti u ON c.campo = u.email
        WHERE c.stato='CLIP_UTENTE' AND c.consenso_social=1 
        ORDER BY c.id DESC
    """

    df_fame = pd.read_sql(query_fame, conn)
    conn.close()

    if not df_fame.empty:
        # Creiamo una lista per ricordarci i video già mostrati
        video_mostrati = []
        
        for i, clip in df_fame.iterrows():
            nome_file = clip['evento']
            
            # Se il video è già stato mostrato in questa pagina, lo saltiamo
            if nome_file in video_mostrati:
                continue
            
            path_fame = os.path.join(CLIP_GDRIVE, nome_file)
            
            if os.path.exists(path_fame):
                st.video(path_fame)
                
                # Aggiungiamo il video alla lista di quelli già visti
                video_mostrati.append(nome_file)
                
                autore = clip['nickname'] if clip['nickname'] else clip['campo']
                st.success(f"⚽ **Azione di: {autore}**")
                
                if clip['ig_tag']:
                    st.caption(f"📸 Segui su Instagram: {clip['ig_tag']}")
                st.divider()

            else:
                st.warning(f"Clip {clip['evento']} in caricamento...")
    else:
        st.info("La Hall of Fame è ancora vuota. Dai il consenso in 'Le Mie Clip'!")

            # --- FINE BLOCCO VISUALIZZAZIONE ---



# --- BOTTONE TORNA ALLA HOME (FINE FILE) ---
if st.button("🔙 Torna alla Home", key="btn_final_back"):
    st.session_state.pagina = 'home_auth' if st.session_state.autenticato else 'home'
    st.rerun()






    # --- ARCHIVIO REGISTRAZIONI EFFETTUATE ---
    st.subheader("🎞️ Archivio Video Registrati")
    conn = sqlite3.connect(DB_PATH)
    # Mostriamo solo quelle con stato 'FATTO' (registrate dal Regista)
    query = "SELECT id, data, campo, ora, evento FROM calendario WHERE stato = 'FATTO' ORDER BY id DESC"
    df_partite = pd.read_sql_query(query, conn)
    conn.close()

    if not df_partite.empty:
        for idx, row in df_partite.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2,2,1,3,1])
            c1.write(f"📅 {row['data']}")
            c2.write(f"🏟️ {row['campo']}")
            c3.write(f"🕒 {row['ora']}")
            c4.write(f"📹 {row['evento']}") # Qui apparirà il nome file match_...
            if c5.button("🗑️", key=f"del_{row['id']}"):
                # Elimina record e file fisico
                if os.path.exists(os.path.join(VIDEO_DIR, row['evento'])):
                    os.remove(os.path.join(VIDEO_DIR, row['evento']))
                conn = sqlite3.connect(DB_PATH); conn.execute("DELETE FROM calendario WHERE id=?", (row['id'],)); conn.commit(); conn.close()
                st.rerun()
    else:
        st.info("Nessuna registrazione completata dal Regista.")


# --- PROFILO ATLETA ---
elif st.session_state.pagina == 'profilo':
    st.markdown("<h2 style='text-align: center;'>👤 Il Tuo Profilo MyPlayr</h2>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    # 1. Recuperiamo i dati dell'utente
    user_query = pd.read_sql("SELECT * FROM utenti WHERE email=?", conn, params=(st.session_state.user_email,))
    
    if not user_query.empty:
        user = user_query.iloc[0]
        
        # --- SEZIONE MODIFICA (FORM) ---
        with st.expander("⚙️ Modifica Dati Profilo e Foto"):
            col_f, col_i = st.columns(2)
            with col_f:
                nuova_foto = st.file_uploader("Aggiorna Foto Profilo", type=['jpg', 'png', 'jpeg'])
            with col_i:
                nuovo_nick = st.text_input("Nickname", value=user['nickname'] if user['nickname'] else "")
                tag_ig_attuale = user['ig_tag'] if 'ig_tag' in user and user['ig_tag'] else ""
                nuovo_ig = st.text_input("Il tuo Tag Instagram (es. @nomeutente)", value=tag_ig_attuale)
                nuovo_ruolo = st.selectbox("Il tuo Ruolo", ["Attaccante", "Centrocampista", "Difensore", "Portiere"])
                nuova_bio = st.text_area("La tua Bio", value=user['bio'] if user['bio'] else "")

            if st.button("💾 SALVA MODIFICHE", use_container_width=True):
                percorso_f = user['foto_path']
                if nuova_foto:
                    percorso_f = os.path.join(IMG_DIR, f"foto_{user['id']}.jpg")
                    with open(percorso_f, "wb") as f:
                        f.write(nuova_foto.getbuffer())
                
                c = conn.cursor()
                c.execute("UPDATE utenti SET nickname=?, ruolo=?, bio=?, foto_path=?, ig_tag=? WHERE email=?", 
                          (nuovo_nick, nuovo_ruolo, nuova_bio, percorso_f, nuovo_ig, st.session_state.user_email))
                conn.commit()
                st.success("✅ Profilo aggiornato!")
                st.rerun()

        st.divider()

        # --- SEZIONE VISUALIZZAZIONE (GRAFICA) ---
        c_left, c_right = st.columns([1, 2])
        with c_left:
            st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
            if user['foto_path'] and os.path.exists(user['foto_path']):
                st.image(user['foto_path'], width=120)
            else:
                st.markdown('<div class="avatar-img">👤</div>', unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top:10px;'><b>{user['nome']} {user['cognome']}</b><br><span style='color:#28a745; font-size:14px; font-weight:bold;'>{user['ruolo']}</span></p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_right:
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f'<div class="data-card"><b>Nickname:</b> {user["nickname"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="data-card"><b>Instagram:</b> {user["ig_tag"] if user["ig_tag"] else "-"}</div>', unsafe_allow_html=True)
            with d2:
                st.markdown(f'<div class="data-card"><b>Ruolo:</b> {user["ruolo"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="data-card"><b>Iscrizione:</b> {user["data_iscrizione"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-card"><b>Email:</b> {st.session_state.user_email}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-card"><b>Bio:</b> {user["bio"]}</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("📊 Le tue statistiche")
        s_cols = st.columns(6)
        st_list = [("🎞️","Clip", "0"), ("⚽","Goal", "0"), ("👟","Assist", "0"), ("🏆","Ranking", "-"), ("🏅","Badge", "0"), ("🔥","Azioni", "0")]
        for i, (ico, tit, val) in enumerate(st_list):
            with s_cols[i]: st.markdown(f'<div class="stat-box">{ico}<br><small>{tit}</small><br><b>{val}</b></div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("🏆 I tuoi trofei")
        st.info("Non hai ancora guadagnato nessun badge.")
        
        st.divider()
        st.subheader("🎥 Clip recenti")
        st.markdown('<p style="text-align:center; padding: 20px; background: #3E444A; border-radius: 10px;">📹<br>Non hai acquistato nessuna clip</p>', unsafe_allow_html=True)
    
    conn.close()

# --- ALTRE PAGINE & FOOTER ---
elif st.session_state.pagina == 'recupero_password': st.button("Torna a login", on_click=lambda: vai_a('login'))
st.markdown("<br><hr><p class='footer-main'> myplayr</p>", unsafe_allow_html=True)
f_l, f_r = st.columns(2)
with f_l: st.markdown("<p class='footer-sub'>Privacy Policy</p>", unsafe_allow_html=True)
with f_r: st.markdown("<p class='footer-sub' style='text-align:right;'>Termini e Condizioni</p>", unsafe_allow_html=True)
st.markdown("<p class='footer-sub' style='text-align:center;'>© 2026 tutti i diritti riservati</p>", unsafe_allow_html=True)









