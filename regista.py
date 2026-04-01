import os
import subprocess
import time
from datetime import datetime
from database import supabase

# Configurazione percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"  # Modifica con il tuo percorso rclone

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)


def trasforma_link_drive(link):
    """
    Trasforma un link Google Drive in formato preview per embedding.
    Es: https://drive.google.com/file/d/ID/view?usp=sharing  ->  https://drive.google.com/file/d/ID/preview
    """
    if "/view" in link:
        return link.replace("/view", "/preview")
    elif "usp=sharing" in link:
        return link.replace("usp=sharing", "preview")
    else:
        return link


def registra_e_carica(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    path_locale = os.path.join(VIDEO_DIR, nome_file)

    print(f"Registrazione video... file: {nome_file}")

    comando_ffmpeg = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', path_locale
    ]

    try:
        subprocess.run(comando_ffmpeg, check=True)

        print("Upload su Google Drive con Rclone...")
        subprocess.run([RCLONE_EXE, "copy", path_locale, "remote:CLIP_MYPLAYR"], check=True)

        # Genera link Google Drive tramite Rclone
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"],
                             capture_output=True, text=True, check=True)
        link_drive = res.stdout.strip()

        link_embed = trasforma_link_drive(link_drive)

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

        print(f"Upload completato, link salvato: {link_embed}")

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

                # Cambia stato in REGISTRAZIONE per evitare doppioni
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", id_p).execute()

                registra_e_carica(id_p)

            else:
                print(f"Nessun match da registrare alle {ora_attuale}")

        except Exception as err:
            print(f"Errore monitor: {err}")

        time.sleep(30)


if __name__ == "__main__":
    monitor()
