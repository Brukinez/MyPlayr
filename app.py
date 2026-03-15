import streamlit as st
import pandas as pd
from supabase import create_client
import time

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="MyPlayr", layout="wide")

SUPABASE_URL = "INSERISCI_URL"
SUPABASE_KEY = "INSERISCI_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_EMAIL = "admin@myplayr.it"

# =========================
# SESSION STATE
# =========================

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

if "autenticato" not in st.session_state:
    st.session_state.autenticato = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# =========================
# NAVIGAZIONE
# =========================

def vai_a(p):
    st.session_state.pagina = p
    st.rerun()

# =========================
# HOME PUBBLICA
# =========================

def pagina_home():

    st.title("⚽ MyPlayr")

    st.markdown("### La piattaforma per rivedere e salvare le tue azioni migliori")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("🔐 Login"):
            vai_a("login")

    with c2:
        if st.button("📝 Registrati"):
            vai_a("registrazione")

    st.divider()

    st.subheader("🏆 Hall of Fame")

    res = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("consenso_social", 1)\
        .order("id", desc=True)\
        .execute()

    df = pd.DataFrame(res.data)

    if not df.empty:
        for i, row in df.head(3).iterrows():
            if row.get("link_video"):
                st.video(row["link_video"])
    else:
        st.info("Nessuna clip ancora disponibile")

# =========================
# HOME UTENTE
# =========================

def pagina_home_auth():

    st.title("🏠 Dashboard MyPlayr")

    st.write(f"Benvenuto **{st.session_state.user_email}**")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("🏟️ Partite"):
            vai_a("partite")

    with c2:
        if st.button("🎞️ Le mie clip"):
            vai_a("mie_clip")

    with c3:
        if st.button("👤 Profilo"):
            vai_a("profilo")

    with c4:
        if st.button("🏆 Hall of Fame"):
            vai_a("hall_of_fame")

    if st.session_state.user_email == ADMIN_EMAIL:
        st.divider()
        if st.button("⚙️ Admin"):
            vai_a("admin")

# =========================
# LOGIN
# =========================

def pagina_login():

    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        res = supabase.table("utenti")\
            .select("*")\
            .eq("email", email)\
            .execute()

        if res.data:
            st.session_state.autenticato = True
            st.session_state.user_email = email
            vai_a("home_auth")
        else:
            st.error("Utente non trovato")

    if st.button("Torna alla Home"):
        vai_a("home")

# =========================
# REGISTRAZIONE
# =========================

def pagina_registrazione():

    st.title("📝 Registrazione")

    email = st.text_input("Email")
    nickname = st.text_input("Nickname")
    password = st.text_input("Password", type="password")

    if st.button("Crea account"):

        supabase.table("utenti").insert({
            "email": email,
            "nickname": nickname
        }).execute()

        st.success("Account creato!")

        time.sleep(1)

        vai_a("login")

# =========================
# PROFILO
# =========================

def pagina_profilo():

    st.title("👤 Profilo")

    email = st.session_state.user_email

    res = supabase.table("utenti")\
        .select("*")\
        .eq("email", email)\
        .execute()

    df = pd.DataFrame(res.data)

    if not df.empty:

        user = df.iloc[0]

        nickname = st.text_input("Nickname", user["nickname"])
        ig = st.text_input("Instagram", user.get("ig_tag", ""))

        if st.button("Salva modifiche"):

            supabase.table("utenti")\
                .update({
                    "nickname": nickname,
                    "ig_tag": ig
                })\
                .eq("email", email)\
                .execute()

            st.success("Profilo aggiornato")

# =========================
# PARTITE
# =========================

def pagina_partite():

    st.title("🏟️ Archivio Partite")

    res = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "FATTO")\
        .order("id", desc=True)\
        .execute()

    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Nessuna partita disponibile")
        return

    for i, row in df.iterrows():

        st.subheader(f"{row['data']} - {row['ora']}")

        if row.get("link_video"):
            st.video(row["link_video"])

            with st.expander("✂️ Crea clip"):

                minuto = st.number_input("Minuto", 0, key=f"m{i}")
                secondo = st.number_input("Secondo", 0, 59, key=f"s{i}")
                durata = st.number_input("Durata", 1, 60, value=10, key=f"d{i}")

                if st.button("Genera clip", key=f"clip{i}"):

                    start = minuto*60 + secondo

                    supabase.table("comandi_clip").insert({
                        "id_partita": row["id"],
                        "inizio_secondi": start,
                        "durata_secondi": durata,
                        "email_utente": st.session_state.user_email,
                        "stato": "RICHIESTO"
                    }).execute()

                    st.success("Richiesta inviata!")

# =========================
# LE MIE CLIP
# =========================

def pagina_mie_clip():

    st.title("🎞️ Le mie clip")

    email = st.session_state.user_email

    res = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("campo", email)\
        .order("id", desc=True)\
        .execute()

    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Non hai ancora clip")
        return

    for i, row in df.iterrows():

        if row.get("link_video"):
            st.video(row["link_video"])

# =========================
# HALL OF FAME
# =========================

def pagina_hall_of_fame():

    st.title("🏆 Hall of Fame")

    res = supabase.table("calendario")\
        .select("*")\
        .eq("stato", "CLIP_UTENTE")\
        .eq("consenso_social", 1)\
        .order("id", desc=True)\
        .execute()

    df = pd.DataFrame(res.data)

    for i, row in df.iterrows():

        if row.get("link_video"):
            st.video(row["link_video"])

# =========================
# ADMIN
# =========================

def pagina_admin():

    if st.session_state.user_email != ADMIN_EMAIL:
        st.error("Accesso non autorizzato")
        return

    st.title("⚙️ Admin MyPlayr")

    st.subheader("Programma partita")

    data = st.date_input("Data")
    ora = st.text_input("Ora")
    campo = st.text_input("Campo")

    if st.button("Salva"):

        supabase.table("calendario").insert({
            "data": data.strftime("%d-%m-%Y"),
            "ora": ora,
            "campo": campo,
            "stato": "PROGRAMMATO"
        }).execute()

        st.success("Partita programmata")

# =========================
# ROUTER
# =========================

pagina = st.session_state.pagina

if pagina == "home":
    pagina_home()

elif pagina == "home_auth":
    pagina_home_auth()

elif pagina == "login":
    pagina_login()

elif pagina == "registrazione":
    pagina_registrazione()

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