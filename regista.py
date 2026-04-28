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

def esegui_taglio_reale(id_partita, inizio, durata, id_richiesta):
    """Esegue il taglio FFmpeg e carica su Drive"""
    try:
        # 1. Trova il file master nella cartella
        file_master = None
        for f in os.listdir(VIDEO_DIR):
            if f.startswith(f"match_{id_partita}_") and f.endswith(".mp4"):
                file_master = f
                break
        
        if not file_master:
            print(f"❌ Master non trovato per partita {id_partita}")
            return None

        input_path = os.path.join(VIDEO_DIR, file_master)
        output_name = f"clip_{id_richiesta}.mp4"
        output_path = os.path.join(VIDEO_DIR, output_name)

        # 2. Comando FFmpeg reale (veloce con -c copy)
        print(f"✂️ Taglio in corso: {output_name}...")
        cmd = [
            'ffmpeg', '-y', '-ss', str(inizio), '-t', str(durata),
            '-i', input_path, '-c', 'copy', '-movflags', '+faststart', output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Upload su Drive
        subprocess.run([RCLONE_EXE, "copy", output_path, "remote:CLIP_MYPLAYR"], check=True)
        
        # 4. Ottieni link e pulisci
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{output_name}"], 
                             capture_output=True, text=True, check=True)
        
        v_id = estrai_id_video(res.stdout.strip())
        link_final = costruisci_link_preview(v_id)

        if os.path.exists(output_path): os.remove(output_path)
        return link_final

    except Exception as e:
        print(f"Errore taglio fisico: {e}")
        return None

def elabora_taglio_clip():
    """Controlla se ci sono richieste di taglio pendenti"""
    try:
        resp = supabase.table("comandi_clip").select("*").eq("stato", "RICHIESTO").execute()
        for req in (resp.data or []):
            print(f"🎬 Elaborazione richiesta {req['id']}...")
            
            link = esegui_taglio_reale(req['id_partita'], req['inizio_secondi'], req['durata_secondi'], req['id'])
            
            if link:
                supabase.table("comandi_clip").update({
                    "url_video": link,
                    "stato": "COMPLETATO"
                }).eq("id", req['id']).execute()
                print(f"✅ Clip completata: {link}")

    except Exception as e:
        print(f"Errore monitor clip: {e}")

def monitor():
    print("🚀 MyClipzo Regista in esecuzione (Registrazione + Taglio)...")
    while True:
        try:
            # --- PARTE 1: REGISTRAZIONE ---
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")
            resp = supabase.table("calendario").select("*").eq("data", data_oggi).eq("ora", ora_attuale).eq("stato", "PROGRAMMATO").execute()

            if resp.data:
                partita = resp.data[0]
                print(f"⚽ Inizio registrazione match: {partita['id']}")
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", partita['id']).execute()
                registra_e_carica(partita['id'])
            
            # --- PARTE 2: TAGLIO CLIP (L'AGGIUNTA FONDAMENTALE) ---
            elabora_taglio_clip()

        except Exception as err:
            print(f"Errore generale: {err}")

        time.sleep(20) # Controllo ogni 20 secondi

if __name__ == "__main__":
    monitor()
