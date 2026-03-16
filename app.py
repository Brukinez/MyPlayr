import streamlit as st
import os
import pandas as pd
import numpy as np
import smtplib
import subprocess
import time
from datetime import datetime
from PIL import Image
from email.mime.text import MIMEText
from database import supabase  # Assicurati che database.py sia presente

# ==========================================
# 1. CONFIGURAZIONE GENERALE E CARTELLE
# ==========================================
st.set_page_config(page_title="MyPlayr - Professional Video Analysis", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
IMG_DIR = os.path.join(BASE_DIR, "PROFILI_FOTO")
CLIP_DIR = os.path.join(BASE_DIR, "CLIP_TAGLIATE")
for f in [VIDEO_DIR, IMG_DIR, CLIP_DIR]:
    os.makedirs(f, exist_ok=True)

CLIP_GDRIVE = r"G:\Il mio Drive\CLIP_MYPLAYR" # Percorso Google Drive
if not os.path.exists(CLIP_GDRIVE):
    try: os.makedirs(CLIP_GDRIVE)
    except: CLIP_GDRIVE = CLIP_DIR

# ==========================================
# 2. STILE CSS PROFESSIONALE (L'estetica del sito)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #2F353B; color: white; }
    h1, h2, h3, p, span, label, .stMarkdown { color: white !important; }
    
    /* Pulsanti VERDI Principali */
    div.stButton > button:first-child {
        background-color: #28a745 !important; color: white !important;
        border: none !important; font-weight: bold !important;
        width: 100%; padding: 12px; border-radius: 8px;
        text-transform: uppercase; font-size: 16px; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #218838 !important; }
    
    /* Layout Cards e Box */
    .data-card { background-color: #3E444A; padding: 15px; border-radius: 8px; border-left: 6px solid #28a745; margin-bottom: 10px; }
    .stat-box { text-align: center; background: #3E444A; padding: 20px; border-radius: 10px; border: 1px solid #28a745; }
    
    /* Avatar e Footer */
    .avatar-img { width: 120px; height: 120px; border-radius: 50%; border: 4px solid #28a745; margin: 0 auto; display: block; }
    .footer-main { text-align: center; font-size: 16px; margin-top: 50px; font-weight: bold; }
    .footer-sub { text-align: center; font-size: 12px; color: #888; }
    hr { border: 1px solid #28a745 !important; opacity: 1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CERVELLO E FUNZIONI (Logica di sistema)
# ==========================================
def inizializza_sessione():
    defaults = {
        'pagina': 'home', 'autenticato': False, 'user_email': "", 
        'user_role': "user", 'user_nick': "Campione", 'password_dev_corretta': False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

inizializza_sessione()

def vai_a(nome):
    st.session_state.pagina = nome

def invia_conferma_e_salva(email_utente):
    email_clean = email_utente.strip().lower()
    try:
        supabase.table("newsletter").insert({"email": email_clean, "data_iscrizione": datetime.now().strftime('%Y-%m-%d %H:%M')}).execute()
        # Logica Email SMTP
        mio_indirizzo, mia_password = "simone.fardella@gmail.com", "xinqcxwubwuasurc"
        msg = MIMEText("Benvenuto in MyPlayr! Il tuo account per la video analisi è attivo.")
        msg['Subject'], msg['From'], msg['To'] = "Benvenuto in MyPlayr", mio_indirizzo, email_clean
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mio_indirizzo, mia_password)
            server.sendmail(mio_indirizzo, email_clean, msg.as_string())
        return True
    except: return False

# ==========================================
# 4. PROTEZIONE SVILUPPATORE (Accesso Area Test)
# ==========================================
if not st.session_state.password_dev_corretta:
    st.markdown("<h1 style='text-align: center;'>🚧 MyPlayr - Area Protetta</h1>", unsafe_allow_html=True)
    st.info("⚠️ Accesso riservato ai test. Inserisci la chiave per sbloccare l'anteprima.")
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        pwd = st.text_input("Password Sviluppatore", type="password", placeholder="Scrivi qui...").strip()
    with col_p2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("SBLOCCA SITO"):
            if pwd.lower() == "myplayr2026":
                st.session_state.password_dev_corretta = True
                st.rerun()
            else: st.error("❌ Chiave Errata!")
    st.stop()

# ==========================================
# 5. NAVBAR DINAMICA (Sincronizzata col Cloud)
# ==========================================
if st.session_state.autenticato:
    is_admin = st.session_state.user_role == "admin"
    nav_cols = st.columns(7 if is_admin else 6)
    with nav_cols[0]: st.button("🏠 Home", on_click=lambda: vai_a('home_auth'))
    with nav_cols[1]: st.button("👤 Profilo", on_click=lambda: vai_a('profilo'))
    with nav_cols[2]: st.button("🏟️ Partite", on_click=lambda: vai_a('partite'))
    with nav_cols[3]: st.button("🏆 Hall", on_click=lambda: vai_a('hall_of_fame'))
    with nav_cols[4]: st.button("🎞️ Clip", on_click=lambda: vai_a('mie_clip'))
    if is_admin:
        with nav_cols[5]: st.button("🛡️ Admin", on_click=lambda: vai_a('admin'))
    with nav_cols[-1]: 
        if st.button("🚪 Esci", type="secondary"):
            st.session_state.autenticato = False
            vai_a('home'); st.rerun()
    st.divider()

# ==========================================
# 6. PAGINA: HOME (La Vetrina)
# ==========================================
if st.session_state.pagina == 'home':
    if os.path.exists("logo.png"):
        _, col_logo, _ = st.columns([1, 1.5, 1])
        with col_logo: st.image("logo.png", use_container_width=True)
    
    st.markdown("<h2 style='text-align: center;'>Gioca. Rivediti. Condividi.</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Il calcio amatoriale e il padel come quelli veri.<br>Ogni azione merita di essere ricordata.</p>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("<h3 style='text-align: center;'>Come Funziona</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success("📹 **GIOCHI**")
        st.write("La nostra AI 4K registra ogni azione da metà campo a 180°.")
    with c2:
        st.success("🔍 **TROVI**")
        st.write("Accedi e trova il tuo match organizzato per data e ora.")
    with c3:
        st.success("📥 **SCARICHI**")
        st.write("Taglia i tuoi momenti migliori e scaricali per i tuoi social.")
    
    st.divider()
    st.markdown("<h3 style='text-align: center;'>Iscriviti alla Newsletter</h3>", unsafe_allow_html=True)
    _, col_news, _ = st.columns([1, 1.5, 1])
    with col_news:
        with st.form("news_form", clear_on_submit=True):
            email_news = st.text_input("Inserisci la tua email").strip().lower()
            if st.form_submit_button("ISCRIVITI ORA"):
                if invia_conferma_e_salva(email_news): st.success("✅ Benvenuto a bordo!")
                else: st.error("❌ Riprova più tardi.")
    
    st.write("<br>", unsafe_allow_html=True)
    _, col_btn_acc, _ = st.columns([1, 1, 1])
    with col_btn_acc:
        st.button("🚀 ACCEDI AL PORTALE", on_click=lambda: vai_a('login'), use_container_width=True)

# ==========================================
# 7. PAGINA: LOGIN / REGISTRAZIONE
# ==========================================
elif st.session_state.pagina == 'login':
    if 'sub' not in st.session_state: st.session_state.sub = 'login'
    _, col_l, _ = st.columns(3)
    with col_log:
        if st.session_state.sub == 'login':
            st.markdown("<h2 style='text-align: center;'>Accedi</h2>", unsafe_allow_html=True)
            u = st.text_input("Email").strip().lower()
            p = st.text_input("Password", type="password")
            if st.button("ENTRA", use_container_width=True):
                if u == "admin@myplayr.com" and p == "admin123":
                    st.session_state.autenticato, st.session_state.user_role, st.session_state.user_nick = True, "admin", "Admin"
                    vai_a('admin'); st.rerun()
                else:
                    res = supabase.table("utenti").select("*").eq("email", u).eq("password", p).execute()
                    if res.data:
                        d = res.data[0]
                        st.session_state.autenticato, st.session_state.user_email = True, d['email']
                        st.session_state.user_role, st.session_state.user_nick = d.get('ruolo', 'user'), d.get('nome', 'Player')
                        vai_a('home_auth'); st.rerun()
                    else: st.error("❌ Credenziali Errate!")
            if st.button("Non hai un account? Registrati", type="secondary"): st.session_state.sub = 'reg'; st.rerun()
        
        elif st.session_state.sub == 'reg':
            st.markdown("<h2 style='text-align: center;'>Registrati</h2>", unsafe_allow_html=True)
            r_n = st.text_input("Nome")
            r_e = st.text_input("Email").strip().lower()
            r_p = st.text_input("Password", type="password")
            if st.button("CONFERMA"):
                supabase.table("utenti").insert({"nome": r_n, "email": r_e, "password": r_p, "ruolo": "user"}).execute()
                st.success("✅ Account creato! Accedi ora.")
                st.session_state.sub = 'login'; st.rerun()
            st.button("🔙 Torna al Login", on_click=lambda: st.session_state.update({"sub": 'login'}))

# ==========================================
# 8. PAGINA: ADMIN (Dashboard & Programmazione)
# ==========================================
elif st.session_state.pagina == 'admin':
    if st.session_state.user_role != "admin": st.error("Accesso Negato"); st.stop()
    
    st.title("🛡️ Dashboard Amministratore")
    # Statistiche
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⚽ Match Totali", "24")
    c2.metric("👥 Utenti", "112")
    c3.metric("🎞️ Clip Tagliate", "450")
    c4.metric("💰 Ricavi", "€1.200")
    
    st.divider()
    # Programmazione
    with st.expander("📅 PROGRAMMA NUOVA REGISTRAZIONE"):
        with st.form("admin_reg"):
            d_g = st.date_input("Data Match", datetime.now())
            o_g = st.text_input("Ora (es: 20:30)")
            c_g = st.selectbox("Campo", ["Campo A", "Campo B", "Padel 1"])
            t_g = st.text_input("Titolo Partita (Squadra A vs Squadra B)")
            if st.form_submit_button("REGISTRA GARA"):
                supabase.table("calendario").insert({"data": d_g.strftime("%d-%m-%Y"), "ora": o_g, "campo": c_g, "evento": t_g, "stato": "PROGRAMMATO"}).execute()
                st.success("✅ Gara salvata sul Cloud!"); st.rerun()

    # Archivio Tabelle
    st.subheader("📊 Riepilogo Attività")
    tab1, tab2 = st.tabs(["Match Fatti", "Clip Utenti"])
    with tab1:
        res_m = supabase.table("calendario").select("*").eq("stato", "FATTO").execute()
        if res_m.data: st.dataframe(pd.DataFrame(res_m.data), use_container_width=True)
    with tab2:
        res_c = supabase.table("calendario").select("*").eq("stato", "CLIP_UTENTE").execute()
        if res_c.data: st.dataframe(pd.DataFrame(res_c.data), use_container_width=True)

# ==========================================
# 9. PAGINA: PARTITE (Editor per l'Utente)
# ==========================================
elif st.session_state.pagina == 'partite':
    st.title("🏟️ Archivio Partite Registrate")
    res_p = supabase.table("calendario").select("*").eq("stato", "FATTO").order("id", desc=True).execute()
    
    if res_p.data:
        for match in res_p.data:
            with st.container():
                st.subheader(f"Gara del {match['data']} ore {match['ora']} - {match['campo']}")
                if match.get('link_video'):
                    st.video(match['link_video'])
                    with st.expander("✂️ CREA LA TUA CLIP"):
                        col1, col2, col3 = st.columns(3)
                        m = col1.number_input("Minuti", 0, 90, key=f"m_{match['id']}")
                        s = col2.number_input("Secondi", 0, 59, key=f"s_{match['id']}")
                        d = col3.number_input("Durata (sec)", 5, 60, 15, key=f"d_{match['id']}")
                        if st.button("🎬 GENERA CLIP ORA", key=f"btn_{match['id']}", use_container_width=True):
                            ts = (m * 60) + s
                            supabase.table("comandi_clip").insert({"id_partita": match['id'], "inizio_secondi": ts, "durata_secondi": d, "email_utente": st.session_state.user_email, "stato": "RICHIESTO"}).execute()
                            st.success("🚀 Richiesta inviata al Mini PC! Controlla 'Le Mie Clip' tra poco.")
                else: st.warning("⚠️ Caricamento video 4K in corso...")
                st.divider()

# ==========================================
# 10. PAGINA: LE MIE CLIP (Download e Social)
# ==========================================
elif st.session_state.pagina == 'mie_clip':
    st.title("🎞️ I Tuoi Highlight Personali")
    res_cl = supabase.table("calendario").select("*").eq("stato", "CLIP_UTENTE").eq("campo", st.session_state.user_email).execute()
    
    if res_cl.data:
        for cl in res_cl.data:
            st.video(cl['link_video'])
            c_d, c_s = st.columns(2)
            with c_d:
                st.markdown(f'<a href="{cl["link_video"]}" target="_blank"><button style="width:100%; background-color:#28a745; color:white; padding:10px; border-radius:8px; font-weight:bold; border:none;">📥 SCARICA VIDEO</button></a>', unsafe_allow_html=True)
            with c_s:
                cons = st.toggle("Mostra in Hall of Fame", value=cl.get('consenso_social', 0)==1, key=f"tg_{cl['id']}")
                if cons != (cl.get('consenso_social', 0)==1):
                    supabase.table("calendario").update({"consenso_social": 1 if cons else 0}).eq("id", cl['id']).execute()
                    st.rerun()
            st.divider()
    else: st.info("Non hai ancora clip. Vai su 'Partite' e crea la tua prima giocata!")

# ==========================================
# 11. HALL OF FAME PRO (Vetrina Social)
# ==========================================
elif st.session_state.pagina == 'hall_of_fame':
    st.title("🏆 MyPlayr Hall of Fame")
    res_h = supabase.table("calendario").select("*, utenti(nome, ig_tag)").eq("stato", "CLIP_UTENTE").eq("consenso_social", 1).execute()
    if res_h.data:
        for h in res_h.data:
            st.video(h['link_video'])
            st.success(f"⚽ Protagonista: **{h.get('utenti', {}).get('nome', h['campo'])}**")
            if h.get('utenti', {}).get('ig_tag'):
                st.caption(f"📸 Instagram: {h['utenti']['ig_tag']}")
            st.divider()

# ==========================================
# 12. FOOTER FINALE (In fondo a tutto)
# ==========================================
st.write("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<p class='footer-main'>MyPlayr - Video Analysis for Future Champions</p>", unsafe_allow_html=True)
st.markdown("<p class='footer-sub'>© 2026 - Tutti i diritti riservati - Privacy Policy | Termini e Condizioni</p>", unsafe_allow_html=True)
