import os
import subprocess
from datetime import datetime
from database import supabase  Per usare la connessione a Supabase

# Cart dove salvi i video localmente (puoi cambiarla se vuoi)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")

# Percorso al programma rclone (modifica con il tuo percorso reale)
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"

if not os.path.existsIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_locale = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"Registrazione video: {nome_file}")
    
    # Comando per registrare con ffmpeg (modifica la webcam se serve)
    comando_ffmpeg = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_locale
    ]

    try:
        # Registra video localmente
        subprocess.run(comando_ffmpeg, check=True)
        print("Video registrato localmente.")

        # Carica video su Google Drive con rclone
        subprocess.run([RCLONE_EXE, "copy", percorso_locale, "remote:CLIP_MYPLAYR"], check=True)
        print("Video caricato su Google Drive.")

        # Genera link al video
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], capture_output=True text=True, check=True)
        link_drive = res_link.stdout.strip()

        # Modifica link per streaming diretto
        link_diretto = link_drive.replace('/view?usp=drivesdk', '').replace('/view', '').replace('file/d/', 'uc?export=download&id=')

        # Aggior Supabase con link e stato "FAT"
        supabase.table("calendario").update({
            "evento": nome_file,
            "link_video": link_diretto,
            "stato": "FATTO"
        }).eq("id", id_partita).execute()

        print(f"Link video aggiornato su Supabase: {link_diretto}")
        return True

    except Exception as e:
        print"Errore durante registrazione o upload: {e}")
        supabase("calendario").update({"stato": "RORE"}).eq("id", id_partita).execute()
        return False
