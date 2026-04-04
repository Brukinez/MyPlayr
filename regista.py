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
    path_locale = os.path.join(VIDEO_DIR, nome_file)
    # 1. Definiamo il percorso (usiamo un nome solo!)
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)

    print(f"🔴 Registrazione video avviata... file: {nome_file}")

    # 2. Creiamo la lista dei comandi (usiamo il nome comando_ffmpeg)
    comando_ffmpeg = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', 
        '-vcodec', 'libx264', 
        '-pix_fmt', 'yuv420p', 
        '-movflags', '+faststart', 
        percorso_completo  # <-- Ora questo nome esiste!
    ]


    try:
        subprocess.run(comando_ffmpeg, check=True)

        print("Upload su Google Drive con Rclone...")
        subprocess.run([RCLONE_EXE, "copy", path_locale, "remote:CLIP_MYPLAYR"], check=True)

        # Genera link Google Drive tramite Rclone
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"],
                             capture_output=True, text=True, check=True)
        link_drive = res.stdout.strip()

        video_id = estrai_id_video(link_drive)
        if not video_id:
            print("Errore: non ho potuto estrarre l'ID video da Google Drive.")
            return False

        link_embed = costruisci_link_preview(video_id)

        # Salva nuovo record nella tabella video
        supabase.table("video").insert({
            "nome_file": nome_file,
            "url_video": link_embed,
            "descrizione": f"Video partita {id_partita}",
            "created_at": datetime.now().isoformat()
        }).execute()

        # Aggiorna tabella calendario con link e stato FATTO
        supabase.table("calendario").update({
            "link_video": link_embed,
            "stato": "FATTO"
        }).eq("id", id_partita).execute()

        print(f"Upload completato, link embed salvato: {link_embed}")

        return True

    except Exception as e:
        print(f"Errore registrazione/upload: {e}")
        supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        return False


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
