# =====================================================
# MYPLAYR - APP PRINCIPALE
# =====================================================

import streamlit as st
import pandas as pd
from database import supabase


# =====================================================
# CONFIG PAGINA
# =====================================================

st.set_page_config(
    page_title="MyPlayr",
    layout="wide"
)


# =====================================================
# SESSION STATE
# =====================================================

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

if "autenticato" not in st.session_state:
    st.session_state.autenticato = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_role" not in st.session_state:
    st.session_state.user_role = "user"


# =====================================================
# NAVIGAZIONE
# =====================================================

def vai_a(pagina):
    st.session_state.pagina = pagina
    st.rerun()


# =====================================================
# NAVBAR
# =====================================================

def navbar():

    if not st.session_state.autenticato:
        return

    is_admin = st.session_state.user_role == "admin"

    cols = st.columns(7 if is_admin else 6)

    with cols[0]:
        st.button("🏠 Home", on_click=lambda: vai_a("home"))

    with cols[1]:
        st.button("👤 Profilo", on_click=lambda: vai_a("profilo"))

    with cols[2]:
        st.button("🏟️ Partite", on_click=lambda: vai_a("partite"))

    with cols[3]:
        st.button("🎬 Le Mie Clip", on_click=lambda: vai_a("mie_clip"))

    with cols[4]:
        st.button("🏆 Hall of Fame", on_click=lambda: vai_a("hall_of_fame"))

    if is_admin:
        with cols[5]:
            st.button("🛡️ Admin", on_click=lambda: vai_a("admin"))

    with cols[-1]:
        if st.button("🚪 Logout"):
            st.session_state.autenticato = False
            st.session_state.user_email = ""
            st.session_state.user_role = "user"
            vai_a("home")

    st.divider()


# =====================================================
# PAGINA HOME
# =====================================================

def pagina_home():

    st.title("🏀 MyPlayr")

    st.write(
        "Benvenuto nella piattaforma MyPlayr. "
        "Rivedi le tue partite, crea clip e condividile."
    )

    if not st.session_state.autenticato:

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):
                vai_a("login")

        with col2:
            if st.button("Registrati"):
                st.info("Registrazione disponibile nel portale.")


# =====================================================
# PAGINA LOGIN
# =====================================================

def pagina_login():

    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Accedi"):

        res = supabase.table("utenti").select("*").eq("email", email).execute()

        if res.data:

            user = res.data[0]

            st.session_state.autenticato = True
            st.session_state.user_email = user["email"]
            st.session_state.user_role = user.get("ruolo", "user")

            st.success("Login effettuato")
            vai_a("home")

        else:
            st.error("Utente non trovato")


# =====================================================
# PAGINA PROFILO
# =====================================================

def pagina_profilo():

    st.title("👤 Profilo")

    email = st.session_state.user_email

    res = supabase.table("utenti").select("*").eq("email", email).execute()

    if not res.data:
        st.error("Profilo non trovato")
        return

    user = res.data[0]

    st.write("Nickname:", user.get("nickname", ""))
    st.write("Instagram:", user.get("ig_tag", ""))


# =====================================================
# PAGINA PARTITE
# =====================================================

def pagina_partite():

    st.title("🏟️ Archivio Partite")

    res = supabase.table("calendario") \
        .select("*") \
        .eq("stato", "FATTO") \
        .order("data", desc=True) \
        .execute()

    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Nessuna partita disponibile.")
        return

    for _, partita in df.iterrows():

        st.subheader(f"{partita['data']} - {partita['evento']}")

        if partita.get("link_video"):
            st.video(partita["link_video"])


# =====================================================
# PAGINA CLIP UTENTE
# =====================================================

def pagina_mie_clip():

    st.title("🎬 Le Mie Clip")

    email = st.session_state.user_email

    res = supabase.table("comandi_clip") \
        .select("*") \
        .eq("email_utente", email) \
        .execute()

    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Non hai ancora creato clip.")
        return

    st.dataframe(df)


# =====================================================
# PAGINA HALL OF FAME
# =====================================================

def pagina_hall_of_fame():

    st.title("🏆 Hall of Fame")

    res = supabase.table("calendario") \
        .select("*") \
        .eq("consenso_social", True) \
        .execute()

    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Nessuna clip condivisa.")
        return

    for _, clip in df.iterrows():

        if clip.get("link_video"):
            st.video(clip["link_video"])


# =====================================================
# PAGINA ADMIN
# =====================================================

def pagina_admin():

    if st.session_state.user_role != "admin":
        st.error("Accesso negato")
        return

    st.title("🛡️ Pannello Admin")

    st.subheader("Programma partita")

    data = st.date_input("Data")
    ora = st.time_input("Ora")
    evento = st.text_input("Evento")

    if st.button("Programma partita"):

        supabase.table("calendario").insert({

            "data": str(data),
            "ora": str(ora),
            "evento": evento,
            "stato": "PROGRAMMATO"

        }).execute()

        st.success("Partita programmata")


# =====================================================
# ROUTER PAGINE
# =====================================================

navbar()

pagina = st.session_state.pagina

if pagina == "home":
    pagina_home()

elif pagina == "login":
    pagina_login()

elif pagina == "profilo":
    pagina_profilo()

elif pagina == "partite":
    pagina_partite()

elif pagina == "mie_clip":
    pagina_mie_clip()

elif pagina == "hall_of_fame":
    pagina_hall_of_fame()

elif pagina == "admin":
    pagina_admin()