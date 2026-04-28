import os
import subprocess
import time
from datetime import datetime
from database import supabase
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"  # Modifica con il tuo percorso

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def estrai_id_video(link_drive):
    """
    Estrae l'ID file da un link Google Drive generico.
    """
    match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", link_drive)
    if match:
        return match.group(1)
    # Prova anche a cercare id nei parametri ?id=...
    import urllib.parse
    parsed = urllib.parse.urlparse(link_drive)
    params = urllib.parse.parse_qs(parsed.query)
    if "id" in params:
        return params["id"][0]
    return None


def costruisci_link_preview(video_id):
    """
    Costruisce il link embed preview da ID video Google Drive.
    """
    return f"https://drive.google.com/file/d/{video_id}/preview"


def registra_e_carica(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    # Questa è la variabile corretta che useremo
    path_locale = os.path.join(VIDEO_DIR, nome_file)

    print(f"Registrazione video... file: {nome_file}")

    # Definizione del comando FFmpeg
    command = [
    'ffmpeg', '-y', 
    '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
    '-t', '30', 
    '-vcodec', 'libx264',   # Formato standard universale
    '-preset', 'veryfast',  # Velocizza la compressione
    '-pix_fmt', 'yuv420p',  # Necessario per i player web
    '-movflags', '+faststart', # Permette al video di partire prima di essere scaricato tutto
    path_locale
]


    try:
        # Eseguiamo il comando usando la variabile 'command'
        subprocess.run(command, check=True)

        print("Upload su Google Drive con Rclone...")
        subprocess.run([RCLONE_EXE, "copy", path_locale, "remote:CLIP_MYPLAYR"], check=True)

        # Otteniamo il link
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"],
                             capture_output=True, text=True, check=True)
        link_drive = res.stdout.strip()

        video_id = estrai_id_video(link_drive)
        if not video_id:
            print("Errore: ID video non estratto.")
            return False

        link_embed = costruisci_link_preview(video_id)

        # Salvataggio su Supabase
        supabase.table("video").insert({
            "nome_file": nome_file,
            "url_video": link_embed,
            "descrizione": f"Video partita {id_partita}"
        }).execute()

        supabase.table("calendario").update({
            "link_video": link_embed,
            "stato": "FATTO"
        }).eq("id", id_partita).execute()

        print(f"Upload completato: {link_embed}")
        return True

    except Exception as e:
        print(f"Errore registrazione/upload: {e}")
        try:
            supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        except:
            pass
        return False

def elabora_taglio_clip():
    """
    Controlla se ci sono richieste di taglio pendenti e le esegue.
    """
    try:
        # Cerca i comandi con stato 'RICHIESTO'
        resp = supabase.table("comandi_clip").select("*").eq("stato", "RICHIESTO").execute()
        richieste = resp.data

        if richieste:
            for req in richieste:
                print(f"🎬 Nuova richiesta di taglio: ID Partita {req['id_partita']} per {req['email_utente']}")
                
                # 1. Recuperiamo il nome del file master dalla tabella calendario o video
                res_v = supabase.table("calendario").select("evento, link_video").eq("id", req['id_partita']).execute()
                if not res_v.data: continue
                
                # Usiamo i dati della richiesta per il taglio
                inizio = req['inizio_secondi']
                durata = req['durata_secondi']
                email = req['email_utente']
                id_req = req['id']

                # --- LOGICA DI TAGLIO (Esempio semplificato, usa il tuo metodo FFmpeg) ---
                # Qui chiameresti una funzione simile a registra_e_carica ma per il taglio
                # Una volta finito l'upload su Drive e ottenuto il link_embed:
                
                link_embed_clip = "https://google.com" # Esempio

                # 2. AGGIORNIAMO SUPABASE: Ora il sito 'vedrà' il video
                supabase.table("comandi_clip").update({
                    "url_video": link_embed_clip,
                    "stato": "COMPLETATO"
                }).eq("id", id_req).execute()
                
                print(f"✅ Clip completata per {email}")

    except Exception as e:
        print(f"Errore elaborazione clip: {e}")



def monitor():
    print("Monitor in esecuzione...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")

            resp = supabase.table("calendario").select("*")\
                .eq("data", data_oggi)\
                .eq("ora", ora_attuale)\
                .eq("stato", "PROGRAMMATO")\
                .execute()

            match_list = resp.data

            if match_list:
                partita = match_list[0]
                id_p = partita['id']
                print(f"Trovato match da registrare: ID {id_p}")
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", id_p).execute()
                registra_e_carica(id_p)
            else:
                print(f"Nessun match da registrare alle {ora_attuale}")

        except Exception as err:
            print(f"Errore monitor: {err}")

        time.sleep(30)

if __name__ == "__main__":
    monitor()
