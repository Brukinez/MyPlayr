import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import smtplib
from email.mime.text import MIMEText
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
# --- NUOVA CONNESSIONE CLOUD ---
from database import supabase  # Importa il collegamento che abbiamo creato prima

# --- REGOLAZIONE LOGO (Cambia questo numero per la grandezza) ---
GRANDEZZA_LOGO = 250  # <--- Prova 350, se è troppo grande metti 300 o 250
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
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO calendario (data, ora, campo, evento, stato) VALUES (?, ?, ?, ?, ?)",
                     (datetime.now().strftime("%d-%m-%Y"), "CLIP", utente_email, nome_output, "CLIP_UTENTE"))
        conn.commit()
        conn.close()
        return output_p # Restituiamo il percorso completo del file su G:
    except:
        return None

# Percorso per salvare le clip su Google Drive (Disco G:)
CLIP_GDRIVE = r"G:\Il mio Drive\CLIP_MYPLAYR"
if not os.path.exists(CLIP_GDRIVE): os.makedirs(CLIP_GDRIVE)



# --- FUNZIONE NEWSLETTER (SUPABASE + EMAIL) ---
def invia_conferma_e_salva(email_utente):
    email_clean = email_utente.strip().lower()

    # 1. SALVATAGGIO SU SUPABASE (Sostituisce il file .txt)
    try:
        supabase.table("newsletter").insert({
            "email": email_clean,
            "data_iscrizione": datetime.now().strftime('%Y-%m-%d %H:%M')
        }).execute()
    except Exception as e:
        print(f"Errore salvataggio database: {e}")
        # Continuiamo comunque con l'invio email anche se il database fallisce

    # 2. CONFIGURAZIONE EMAIL (I tuoi dati sono corretti)
    mio_indirizzo = "simone.fardella@gmail.com"  
    mia_password = "xinqcxwubwuasurc"   
    
    msg = MIMEText(f"Grazie per esserti iscritto alla newsletter di MyPlayr!")
    msg['Subject'] = "Conferma Iscrizione MyPlayr"
    msg['From'] = mio_indirizzo
    msg['To'] = email_clean

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mio_indirizzo, mia_password)
            server.sendmail(mio_indirizzo, email_clean, msg.as_string())
        return True
    except Exception as e:
        print(f"Errore invio email: {e}")
        return False


# --- CONFIGURAZIONE PERCORSI ---
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Percorsi per i file temporanei o immagini
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")

# ✅ ELIMINATO DB_PATH (Ora usiamo Supabase nel cloud)

# Creazione cartelle (Necessario solo per il Mini PC o caricamenti temporanei)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)


# --- FUNZIONI DATABASE CLOUD (SUPABASE) ---

def get_utente_per_email(email):
    """Cerca un utente nel Cloud tramite email"""
    email_clean = email.strip().lower()
    try:
        res = supabase.table("utenti").select("*").eq("email", email_clean).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Errore connessione database: {e}")
        return None

def crea_nuovo_utente(dati_utente):
    """Registra un nuovo utente nel Cloud"""
    try:
        # Assicurati che l'email sia sempre pulita prima del salvataggio
        dati_utente["email"] = dati_utente["email"].strip().lower()
        res = supabase.table("utenti").insert(dati_utente).execute()
        return True
    except Exception as e:
        st.error(f"Errore durante la registrazione: {e}")
        return False

    
    # --- CONFIGURAZIONE PERCORSI ---
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Percorsi per i file temporanei o immagini
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")

# ✅ ELIMINATO DB_PATH (Ora usiamo Supabase nel cloud)

# Creazione cartelle (Necessario solo per il Mini PC o caricamenti temporanei)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# --- GESTIONE PROFILO UTENTE (SUPABASE) ---

def aggiorna_profilo_social(email, nuovo_tag_ig):
    """Aggiorna il tag Instagram dell'utente nel Cloud"""
    try:
        email_clean = email.strip().lower()
        supabase.table("utenti").update({"ig_tag": nuovo_tag_ig}).eq("email", email_clean).execute()
        st.success("✅ Profilo Instagram aggiornato!")
    except Exception as e:
        st.error(f"Errore durante l'aggiornamento: {e}")

def ottieni_dati_profilo(email):
    """Recupera tutte le info dell'utente (Bio, IG, Foto) dal Cloud"""
    email_clean = email.strip().lower()
    res = supabase.table("utenti").select("*").eq("email", email_clean).execute()
    return res.data[0] if res.data else None



# --- PROTEZIONE SITO (PASSWORD SVILUPPATORE) ---
if "password_dev_corretta" not in st.session_state:
    st.session_state["password_dev_corretta"] = False

if not st.session_state["password_dev_corretta"]:
    st.markdown("<h1 style='text-align: center;'>🚧 MyPlayr - Area Protetta</h1>", unsafe_allow_html=True)
    st.info("Il sito è in fase di test. Inserisci la password per sbloccare l'anteprima.")
    
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        # Usiamo .strip() per evitare errori se l'utente mette uno spazio per sbaglio
        pwd_inserita = st.text_input("Password Sviluppatore", type="password", placeholder="Scrivi qui...").strip()
    with col_p2:
        st.write("<br>", unsafe_allow_html=True) 
        if st.button("SBLOCCA SITO"):
            # Controllo password (puoi cambiarla qui o metterla nei Secrets)
            if pwd_inserita.lower() == "myplayr2026": 
                st.session_state["password_dev_corretta"] = True
                st.rerun()
            else:
                st.error("❌ Password errata!")
    st.stop() 


# --- LOGICA NAVIGAZIONE E SESSIONE ---
if 'pagina' not in st.session_state: 
    st.session_state.pagina = 'home'
if 'autenticato' not in st.session_state: 
    st.session_state.autenticato = False
if 'user_email' not in st.session_state: 
    st.session_state.user_email = ""
if 'user_role' not in st.session_state: # <--- Fondamentale per distinguere Admin/Giocatore
    st.session_state.user_role = "user"
if 'user_nick' not in st.session_state: # <--- Per visualizzare il nome in alto
    st.session_state.user_nick = ""
if 'editing' not in st.session_state: 
    st.session_state.editing = False

def vai_a(nome):
    st.session_state.pagina = nome
    # Non serve rerun() qui se vai_a viene chiamata dentro un evento pulsante


# --- NAVBAR DINAMICA (SUPABASE READY) ---
if st.session_state.autenticato:
    # Usiamo il 'ruolo' salvato nel session_state invece della sola email
    is_admin = st.session_state.get('user_role') == "admin"
    
    # Creiamo le colonne: 7 per l'Admin (ha il tasto in più), 6 per l'Utente
    nav_cols = st.columns(7 if is_admin else 6)
    
    with nav_cols[0]: st.button("🏠 Home", on_click=lambda: vai_a('home_auth'))
    with nav_cols[1]: st.button("👤 Profilo", on_click=lambda: vai_a('profilo'))
    with nav_cols[2]: st.button("🏟️ Partite", on_click=lambda: vai_a('partite'))
    with nav_cols[3]: st.button("🏆 Hall of Fame", on_click=lambda: vai_a('hall_of_fame'))
    with nav_cols[4]: st.button("🎞️ Le Mie Clip", on_click=lambda: vai_a('mie_clip'))
    
    # Tasto Admin visibile solo se il ruolo su Supabase è 'admin'
    if is_admin:
        with nav_cols[5]: st.button("🛡️ Admin", on_click=lambda: vai_a('admin'))
    
    # Il tasto Logout è sempre l'ultimo
    with nav_cols[-1]: 
        if st.button("🚪 Esci", type="secondary"): # 'secondary' per non farlo troppo invasivo
            # Puliamo la sessione al logout
            st.session_state.autenticato = False
            st.session_state.user_email = ""
            st.session_state.user_role = "user"
            vai_a('home')
            
    st.divider() # Linea verde di separazione (dal tuo CSS)

# --- PAGINA: HALL OF FAME (PUBBLICA - SUPABASE READY) ---
elif st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>🏆 MyPlayr Hall of Fame</h1>", unsafe_allow_html=True)
    st.write("---")

    # 1. Recupero dati da Supabase invece di SQLite
    # Cerchiamo solo le clip che hanno lo stato 'CLIP_UTENTE' e il consenso attivo
    response = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("consenso_social", 1)\
        .execute()
    
    clip_visibili = pd.DataFrame(response.data)

    # --- SPIE DI CONTROLLO (DEBUG) ---
    if not clip_visibili.empty:
        st.success(f"✅ Ci sono {len(clip_visibili)} azioni spettacolari nella Hall of Fame!")
        
        for i, clip in clip_visibili.iterrows():
            # 2. Usiamo il link_video (URL Cloud) invece del percorso locale G:
            url_video = clip.get('link_video')
            
            with st.container():
                if url_video:
                    # Visualizzazione tramite URL (Funziona su smartphone e PC)
                    st.video(url_video)
                    st.write(f"🏟️ Campo: **{clip['campo']}**")
                    if clip.get('evento'):
                        st.caption(f"🎬 Azione: {clip['evento']}")
                else:
                    st.warning(f"⚠️ Link video non disponibile per la clip ID: {clip['id']}")
                st.divider()
    else:
        st.info("📌 La Hall of Fame è temporaneamente vuota. Carica le tue prodezze per apparire qui!")


# --- PAGINA 1: HOME PAGE (INTEGRALE - SUPABASE READY) ---
elif st.session_state.pagina == 'home':
    # 1. LOGO CENTRATO (Gestione sicura del file)
    if os.path.exists("logo.png"):
        _, col_logo, _ = st.columns([1, 2, 1])
        with col_logo:
            st.image("logo.png", use_container_width=True)
    
    st.write(" ") # Spaziatura

    # Mostra i contenuti solo se l'utente NON è ancora autenticato
    if not st.session_state.autenticato:
        st.markdown("<h2 style='text-align: center;'>Gioca. Rivediti. Condividi.</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 16px;'>Ogni partita merita di essere ricordata!<br>Il calcio amatoriale come quello vero.<br>Condividi le tue giornate con amici, famiglia e sui social media.</p>", unsafe_allow_html=True)
        
        # --- SEZIONE COME FUNZIONA ---
        st.markdown("<h2 style='text-align: center;'>Come Funziona</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.success("📹 **Giochi la Partita**")
            st.markdown("<p style='font-size: 14px;'>Scendi in campo e gioca. Ogni azione viene registrata in HD.</p>", unsafe_allow_html=True)
        with c2:
            st.success("🔍 **Trovi il Video**")
            st.markdown("<p style='font-size: 14px;'>Accedi al portale e trova i video organizzati per data e campo.</p>", unsafe_allow_html=True)
        with c3:
            st.success("📥 **Scarichi la Clip**")
            st.markdown("<p style='font-size: 14px;'>Taglia i tuoi momenti migliori e scarica le clip per i social.</p>", unsafe_allow_html=True)
            
        # --- SEZIONE NEWSLETTER (COLLEGATA A SUPABASE) ---
        st.markdown("<h3 style='text-align: center;'>Resta in contatto</h3>", unsafe_allow_html=True)
        _, col_news, _ = st.columns([1, 2, 1])
        with col_news:
            with st.form("newsletter_form", clear_on_submit=True):
                # Usiamo .strip().lower() per pulire l'input subito
                email_input = st.text_input("La tua mail", placeholder="esempio@mail.com").strip().lower()
                submit_button = st.form_submit_button("ISCRIVITI ORA")
                
                if submit_button:
                    if "@" in email_input and "." in email_input:
                        # Qui chiamiamo la funzione che salva su Supabase (quella vista prima)
                        successo = invia_conferma_e_salva(email_input)
                        if successo:
                            st.success("✅ Iscrizione salvata! Riceverai le novità.")
                        else:
                            st.warning("⚠️ Salvato nel database, ma l'email di conferma ha avuto un ritardo.")
                    else:
                        st.error("❌ Inserisci un'email valida.")

        # --- TASTO ACCESSO FINALE ---
        st.write("<br>", unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            # Questo tasto porta l'utente alla pagina di Login reale
            st.button("🚀 ACCEDI AL PORTALE", on_click=lambda: vai_a('login'))

# --- PAGINA: LOGIN / REGISTRAZIONE / RECUPERO ---
elif st.session_state.pagina == 'login':
    _, col_log, _ = st.columns(3)
    with col_log:
        # Inizializzazione dello stato interno (Login / Reg / Recupero)
        if 'sub' not in st.session_state: 
            st.session_state.sub = 'login'

        # --- 1. SOTTO-PAGINA: ACCEDI (Modulo Standard) ---
        if st.session_state.sub == 'login':
            st.markdown("<h2 style='text-align: center;'>Accedi</h2>", unsafe_allow_html=True)
            u = st.text_input("Email").strip().lower()
            p = st.text_input("Password", type="password")
            
            if st.button("ENTRA"):
                # Sostituito SQLite con Supabase: Cerchiamo l'utente
                res = supabase.table("utenti").select("*").eq("email", u).eq("password", p).execute()
                
                # Controllo Admin manuale (come avevi tu) o utente trovato nel DB
                if (u == "admin@myplayr.com" and p == "admin123") or (res.data and len(res.data) > 0):
                    st.session_state.autenticato = True
                    st.session_state.user_email = u
                    # Recuperiamo il ruolo dal DB se esiste, altrimenti 'Player'
                    role = res.data[0].get('ruolo', 'Player') if res.data else 'admin'
                    st.session_state.user_role = role
                    vai_a('profilo')
                else: 
                    st.error("Credenziali errate!")
            
            # Pulsanti di scambio (Mantengono la tua logica originale)
            if st.button("password dimenticata?", type="secondary"): 
                st.session_state.sub = 'recupero'
                st.rerun()
            if st.button("Non hai ancora un account? Registrati", type="secondary"):
                st.session_state.sub = 'reg'
                st.rerun()
            st.button("🔙 INDIETRO", on_click=lambda: vai_a('home'))

        # --- 2. SOTTO-PAGINA: REGISTRAZIONE (Sostituisce il Login) ---
        elif st.session_state.sub == 'reg':
            st.markdown("<h2 style='text-align: center;'>Registrati</h2>", unsafe_allow_html=True)
            r_n = st.text_input("Nome")
            r_c = st.text_input("Cognome")
            r_e = st.text_input("Email").strip().lower()
            r_p = st.text_input("Password", type="password")
            
            if st.button("CONFERMA REGISTRAZIONE"):
                if r_n and r_c and r_e and r_p:
                    # Sostituito SQLite con Supabase: Inserimento Cloud
                    nuovo_utente = {
                        "nome": r_n, 
                        "cognome": r_c, 
                        "email": r_e, 
                        "password": r_p, 
                        "ruolo": "Player"
                    }
                    try:
                        supabase.table("utenti").insert(nuovo_utente).execute()
                        st.success("✅ Account creato!")
                        st.session_state.sub = 'login'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")
                else: 
                    st.error("Riempi tutti i campi")
            
            if st.button("🔙 TORNA AL LOGIN", type="secondary"): 
                st.session_state.sub = 'login'
                st.rerun()

        # --- 3. SOTTO-PAGINA: RECUPERO (Sostituisce il Login) ---
        elif st.session_state.sub == 'recupero':
            st.markdown("<h2 style='text-align: center;'>Recupero</h2>", unsafe_allow_html=True)
            m_rec = st.text_input("Inserisci la tua Email").strip().lower()
            if st.button("INVIA PASSWORD"):
                # Qui potrai collegare la funzione newsletter per inviare la mail
                st.info("Email inviata (funzione in test)")
            if st.button("🔙 TORNA AL LOGIN", type="secondary"): 
                st.session_state.sub = 'login'
                st.rerun()


# --- PAGINA ADMIN (DASHBOARD COMPLETA - SUPABASE READY) ---
elif st.session_state.pagina == 'admin':
    # 1. Recupero dati reali dal Cloud (Supabase)
    res_utenti = supabase.table("utenti").select("id", count="exact").execute()
    num_utenti = res_utenti.count if res_utenti.count else 0
    
    res_partite = supabase.table("calendario").select("id", count="exact").execute()
    num_partite = res_partite.count if res_partite.count else 0
    
    res_news = supabase.table("newsletter").select("id", count="exact").execute()
    num_newsletter = res_news.count if res_news.count else 0

    st.title("📊 Dashboard Amministratore")

    # 2. Riga dei contatori (Cards) - Fedele al tuo layout
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("⚽ Partite", num_partite)
    with c2: st.metric("🎞️ Clip Visitate", "0")
    with c3: st.metric("💰 Ricavi", "€0.00")
    with c4: st.metric("👥 Giocatori", num_utenti)
    with c5: st.metric("📧 Newsletter", num_newsletter)
    with c6: st.metric("📈 Conv. Rate", "0.0%")

    st.divider()

    # 3. Grafico e Azioni Rapide (Mantenuti come da tua richiesta)
    col_graf, col_act = st.columns(2)
    with col_graf:
        st.subheader("📈 Ricavi (7gg)")
        dati_grafico = pd.DataFrame({"G": ["L", "M", "M", "G", "V", "S", "D"], "€": [10, 45, 30, 80, 60, 120, 90]})
        st.line_chart(dati_grafico, x="G", y="€", color="#28a745")
    with col_act:
        st.subheader("⚡ Azioni Rapide")
        ca, cb = st.columns(2)
        with ca:
            st.button("📧 Invia Newsletter", use_container_width=True)
            if st.button("📂 Export Utenti CSV", use_container_width=True):
                # Esempio rapido export
                df_csv = pd.DataFrame(supabase.table("utenti").select("*").execute().data)
                st.download_button("Scarica CSV", df_csv.to_csv(), "utenti.csv")
        with cb:
            st.button("🧹 Pulisci Cache", use_container_width=True)
            st.button("📊 Report Mensile", use_container_width=True)

    st.divider()

    # 4. Top 5 e Richieste Clip (Dati simulati mantenuti per ora)
    col_top, col_req = st.columns(2)
    with col_top:
        st.subheader("🏆 Top 5 Giocatori")
        st.table(pd.DataFrame({"USER": ["Bomber9", "Alex_G", "Simo_F", "Luca_S", "Pippo_I"], "TOT": ["€120", "€85", "€70", "€55", "€40"]}))
    with col_req:
        st.subheader("📩 Richieste Recenti")
        # Qui in futuro leggeremo la tabella 'comandi_clip'
        st.info("Richiesta: Alex_Goal (03/03)")
        st.info("Richiesta: Bomber99 (04/03)")

    st.divider()

    # --- 5. VISUALIZZAZIONE VIDEO REGISTRATI (Admin) ---
    st.subheader("🎞️ Archivio Registrazioni Completate")
    
    # Recuperiamo i match 'FATTO' dal Cloud
    res_fatto = supabase.table("calendario")\
        .select("id, data, campo, ora, evento, link_video")\
        .eq("stato", "FATTO")\
        .order("id", desc=True)\
        .execute()
    
    df_partite = pd.DataFrame(res_fatto.data)

    if not df_partite.empty:
        for idx, row in df_partite.iterrows():
            with st.container():
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.write(f"📅 **{row['data']}** | 🏟️ {row['campo']} | 🕒 {row['ora']}")
                    st.write(f"📄 File: `{row['evento']}`")
                    if row['link_video']:
                        st.video(row['link_video']) # L'Admin può vedere il video direttamente dal Cloud!
                with col_del:
                    if st.button("🗑️", key=f"del_adm_{row['id']}"):
                        # Eliminiamo la riga su Supabase
                        supabase.table("calendario").delete().eq("id", row['id']).execute()
                        st.success("Riga eliminata!")
                        st.rerun()
                st.divider()
    else:
        st.info("Nessun video registrato presente nel Cloud.")

    # --- PROGRAMMAZIONE REGISTRAZIONE (Solo per Admin - SUPABASE READY) ---
st.divider()
with st.expander("📅 PROGRAMMA NUOVA REGISTRAZIONE", expanded=False):
    with st.form("form_admin_reg"):
        d_reg = st.date_input("Giorno Gara", datetime.now())
        f_ora = st.text_input("Ora Inizio (es: 19:30)")
        f_titolo = st.text_input("Titolo Partita (Squadre)")
        
        if st.form_submit_button("CONFERMA PROGRAMMAZIONE"):
            # Salvataggio su Supabase invece di SQLite
            nuovo_match = {
                "data": d_reg.strftime('%d-%m-%Y'),
                "ora": f_ora,
                "campo": "Campo A", # Puoi renderlo dinamico se hai più campi
                "evento": f_titolo,
                "stato": "PROGRAMMATO"
            }
            try:
                supabase.table("calendario").insert(nuovo_match).execute()
                st.success("✅ Gara programmata sul Cloud! Il Mini PC la caricherà a breve.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")

st.divider()

# --- 6. ARCHIVIO VIDEO TOTALE (VISTA TABELLARE) ---
st.subheader("🎞️ Archivio Video Totale")

# 1. Recupero PARTITE INTERE (stato 'FATTO')
st.markdown("### 🏟️ Archivio Partite Registrate")
res_vids = supabase.table("calendario").select("id, data, ora, campo, evento, link_video").eq("stato", "FATTO").order("id", desc=True).execute()
df_vids = pd.DataFrame(res_vids.data)

if not df_vids.empty:
    st.dataframe(df_vids[['id', 'data', 'ora', 'campo', 'evento']], use_container_width=True)
else:
    st.info("Nessuna partita intera registrata al momento.")

# 2. Recupero CLIP TAGLIATE (stato 'CLIP_UTENTE')
st.markdown("### ✂️ Archivio Clip Tagliate dagli Utenti")
res_clips = supabase.table("calendario").select("id, data, campo, evento").eq("stato", "CLIP_UTENTE").order("id", desc=True).execute()
df_clips_admin = pd.DataFrame(res_clips.data)

if not df_clips_admin.empty:
    # Rinominiamo le colonne per chiarezza come nel tuo codice originale
    df_visualizza = df_clips_admin.rename(columns={'campo': 'utente', 'evento': 'nome_clip'})
    st.dataframe(df_visualizza, use_container_width=True)
else:
    st.info("Nessun utente ha ancora tagliato delle clip.")

st.divider()

# --- 7. GESTIONE SINGOLI VIDEO (Cancellazione) ---
st.subheader("🗑️ Gestione Rapida Archivio")
if not df_vids.empty:
    for idx, row in df_vids.iterrows():
        c1, c2, c3, c4, c5 = st.columns([1.5, 2, 1.5, 3.5, 1])
        c1.write(f"📅 {row['data']}")
        c2.write("🏟️ Campo A")
        c3.write(f"🕒 {row['ora']}")
        c4.write(row['evento'] if row['evento'] else "In elaborazione...")
        
        if c5.button("🗑️", key=f"del_g_{row['id']}"):
            # Eliminiamo la riga dal database Cloud
            try:
                supabase.table("calendario").delete().eq("id", row['id']).execute()
                st.success(f"Match {row['id']} rimosso dal portale.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'eliminazione: {e}")
else:
    st.info("Nessun video registrato in archivio.")




    # --- 7. BOTTONE INDIETRO (NAVIGAZIONE ADMIN) ---
st.write(" ") # Un po' di spazio prima del tasto
if st.button("🔙 Torna alla Home", key="back_adm"):
    # Reindirizza alla Home per utenti loggati
    vai_a('home_auth')


# --- PAGINA PARTITE (PROGRAMMAZIONE + ARCHIVIO + TAGLIO) ---
elif st.session_state.pagina == "Pannello Admin":
    st.title("⚙️ Controllo MyPlayr (Riservato)")
    
    # 1. FORM PROGRAMMAZIONE (Sincronizzato con Supabase)
    with st.form("programma_match"):
        data_p = st.date_input("Data", key="admin_data")
        ora_p = st.text_input("Ora (es. 15:30)", key="admin_ora")
        campo_p = st.text_input("Campo", key="admin_campo")
        if st.form_submit_button("🔴 CONFERMA PROGRAMMAZIONE"):
            # Scrittura su Supabase
            supabase.table("calendario").insert({
                "data": data_p.strftime("%d-%m-%Y"),
                "ora": ora_p,
                "campo": campo_p,
                "stato": 'PROGRAMMATO'
            }).execute()
            st.success(f"✅ Registrazione programmata alle {ora_p} sul Cloud!")
            st.rerun()

    st.divider()

    # 2. VISUALIZZAZIONE PARTITE REGISTRATE E TAGLIO CLIP
    st.markdown("### 🎞️ Partite Disponibili")
    
    # Recuperiamo le partite 'FATTO' da Supabase
    res = supabase.table("calendario").select("*").eq("status", "FATTO").order("id", desc=True).execute()
    df_partite = pd.DataFrame(res.data)

    if df_partite.empty:
        st.info("Nessuna partita registrata trovata nel Cloud.")
    else:
        for index, row in df_partite.iterrows():
            st.subheader(f"🏟️ Partita: {row['data']} - {row['ora']} ({row['campo']})")
            
            video_url = row.get('link_video') # URL pubblico di Google Drive (generato dal Mini PC)

            if video_url:
                # Visualizziamo il video dal Cloud (Funziona ovunque!)
                st.video(video_url)
                
                # Box per il taglio della clip (LOGICA ASINCRONA)
                with st.expander("✂️ CREA LA TUA CLIP PERSONALIZZATA"):
                    st.write("Scegli il momento dell'azione:")
                    c1, col_s, c3 = st.columns(3)
                    with c1:
                        m_in = st.number_input("Minuto inizio", min_value=0, step=1, key=f"min_{row['id']}")
                    with col_s:
                        s_in = st.number_input("Secondo inizio", min_value=0, max_value=59, step=1, key=f"sec_{row['id']}")
                    with c3:
                        durata_clip = st.number_input("Durata (sec)", min_value=1, max_value=60, value=10, key=f"dur_{row['id']}")

                    if st.button("🎬 RICHIEDI TAGLIO CLIP", key=f"req_{row['id']}", type='primary', use_container_width=True):
                        inizio_tot = (m_in * 60) + s_in
                        
                        # Invece di tagliare subito, mandiamo un comando al Mini PC tramite Supabase
                        supabase.table("comandi_clip").insert({
                            "id_partita": row['id'],
                            "inizio_secondi": inizio_tot,
                            "durata_secondi": durata_clip,
                            "email_utente": st.session_state.user_email,
                            "stato": "RICHIESTO"
                        }).execute()
                        
                        st.success("✅ Richiesta inviata! Il Mini PC sta preparando la tua clip. La troverai tra poco in 'Le Mie Clip'.")
            else:
                st.warning("⚠️ Video in fase di caricamento sul Cloud... Riprova tra poco.")
            
            st.divider()


# --- PAGINA PARTITE (VISIBILE A TUTTI - SUPABASE READY) ---
elif st.session_state.pagina == 'partite':
    st.title("🏟️ Archivio Partite MyPlayr")
    
    # 1. Recupero dati da Supabase (Niente più SQLite locale)
    res = supabase.table("calendario").select("*").eq("stato", "FATTO").order("id", desc=True).execute()
    df_partite = pd.DataFrame(res.data)

    if df_partite.empty:
        st.info("📌 Nessuna partita ancora disponibile. Torna a trovarci dopo il prossimo match!")
    else:
        for index, row in df_partite.iterrows():
            st.subheader(f"📅 Partita del {row['data']} - Ore {row['ora']}")
            
            # Recuperiamo il link pubblico generato da Rclone
            video_url = row.get('link_video') 

            if video_url:
                # Mostriamo il video in streaming (Funziona su smartphone!)
                st.video(video_url)
                
                # --- BOX PER IL TAGLIO ASINCRONO ---
                with st.expander("✂️ CREA LA TUA CLIP PERSONALIZZATA"):
                    st.write("Seleziona l'azione che vuoi salvare:")
                    c1, col_s, c3 = st.columns(3)
                    with c1:
                        m_in = st.number_input("Minuto inizio", min_value=0, step=1, key=f"min_u_{row['id']}")
                    with col_s:
                        s_in = st.number_input("Secondo inizio", min_value=0, max_value=59, step=1, key=f"sec_u_{row['id']}")
                    with c3:
                        durata_clip = st.number_input("Durata (sec)", min_value=1, max_value=60, value=10, key=f"dur_u_{row['id']}")

                    if st.button("🎬 GENERA CLIP", key=f"btn_u_{row['id']}", use_container_width=True, type='primary'):
                        inizio_tot = (m_in * 60) + s_in
                        
                        # MANDIAMO IL COMANDO AL MINI PC TRAMITE SUPABASE
                        # Il Mini PC ha il file originale sul disco G: e farà il taglio fisico
                        supabase.table("comandi_clip").insert({
                            "id_partita": row['id'],
                            "inizio_secondi": inizio_tot,
                            "durata_secondi": durata_clip,
                            "email_utente": st.session_state.user_email.strip().lower(),
                            "stato": "RICHIESTO"
                        }).execute()
                        
                        st.success("🚀 Richiesta inviata al sistema centrale! La tua clip sarà pronta tra pochi minuti nella sezione 'Le Mie Clip'.")
            else:
                st.warning(f"⚠️ Il video è in fase di elaborazione nel Cloud. Riprova tra poco!")
            
            st.divider()

# --- PAGINA: LE MIE CLIP (VISIBILE ALL'UTENTE - SUPABASE READY) ---
elif st.session_state.pagina == 'mie_clip':
    st.markdown("<h2 style='text-align: center;'>🎞️ I Tuoi Highlight</h2>", unsafe_allow_html=True)
    
    # 1. Recupero clip personali da Supabase
    # Filtriamo per l'email dell'utente loggato
    email_u = st.session_state.user_email.strip().lower()
    res = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("campo", email_u)\
        .order("id", desc=True)\
        .execute()
    
    mie_clip = pd.DataFrame(res.data)

    if not mie_clip.empty:
        for index, row_c in mie_clip.iterrows():
            url_clip = row_c.get('link_video') # URL pubblico Cloud
            nome_file = row_c.get('evento', 'myplayr_clip.mp4')
            
            with st.container():
                if url_clip:
                    # Visualizzazione Video dal Cloud
                    st.video(url_clip)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        # Il download ora punta al link web, non al file locale G:
                        st.markdown(f"""
                            <a href="{url_clip}" target="_blank" style="text-decoration: none;">
                                <button style="width:100%; background-color:#28a745; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">
                                    📥 SCARICA CLIP
                                </button>
                            </a>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        # Gestione Consenso Social (Hall of Fame)
                        stato_db = True if row_c.get('consenso_social', 0) == 1 else False
                        consenso = st.toggle("Sì, pubblicami su @MyPlayr", value=stato_db, key=f"tog_{row_c['id']}")
                        
                        if consenso != stato_db:
                            nuovo_valore = 1 if consenso else 0
                            # Aggiornamento immediato su Supabase
                            supabase.table("calendario").update({"consenso_social": nuovo_valore}).eq("id", row_c['id']).execute()
                            st.toast("✅ Impostazioni social aggiornate!")
                            time.sleep(0.5)
                            st.rerun()
                            
                    if stato_db:
                        st.success("✨ Questa clip è visibile nella Hall of Fame!")
                else:
                    st.warning(f"⏳ La clip '{nome_file}' è in fase di generazione dal Mini PC...")
                st.divider()
    else:
        st.info("💡 Non hai ancora creato nessuna clip. Vai nella sezione 'Partite' per tagliare i tuoi momenti migliori!")




# --- PAGINA: HALL OF FAME (PUBBLICA - SUPABASE READY) ---
elif st.session_state.pagina == 'hall_of_fame':
    st.markdown("<h1 style='text-align: center;'>🏆 MyPlayr Hall of Fame</h1>", unsafe_allow_html=True)
    st.divider()

    # 1. Recupero dati con Join (Video + Info Utente) da Supabase
    # Nota: Supabase gestisce le relazioni automaticamente se le tabelle sono collegate
    res = supabase.table("calendario")\
        .select("evento, campo, consenso_social, stato, link_video, utenti(nickname, ig_tag)")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("consenso_social", 1)\
        .order("id", desc=True)\
        .execute()
    
    df_fame = pd.DataFrame(res.data)

    if not df_fame.empty:
        # Lista per evitare duplicati (come nel tuo codice originale)
        video_mostrati = []
        
        for i, clip in df_fame.iterrows():
            nome_file = clip['evento']
            url_video = clip.get('link_video') # URL pubblico Cloud
            
            if nome_file in video_mostrati:
                continue
            
            if url_video:
                # Visualizzazione Video dal Cloud (Funziona ovunque)
                st.video(url_video)
                video_mostrati.append(nome_file)
                
                # Recupero info autore (Nickname o Email)
                info_utente = clip.get('utenti', {}) # Dati dalla JOIN
                autore = info_utente.get('nickname') if info_utente and info_utente.get('nickname') else clip['campo']
                
                st.success(f"⚽ **Azione di: {autore}**")
                
                # Mostra Tag Instagram se presente
                ig = info_utente.get('ig_tag') if info_utente else None
                if ig:
                    st.caption(f"📸 Segui su Instagram: {ig}")
                st.divider()
            else:
                st.warning(f"⏳ La clip '{nome_file}' è in fase di caricamento...")
    else:
        st.info("📌 La Hall of Fame è ancora vuota. Dai il consenso in 'Le Mie Clip' per apparire qui!")


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









