import re
import os
import subprocess
from datetime import datetime
from glob import glob
from database import supabase

# Si assume che queste variabili siano già definite a livello modulo (no hardcoding nel codice):
# VIDEO_DIR, CLIP_DIR, RCLONE_EXE, DRIVE_REMOTE, DRIVE_IN, DRIVE_OUT

# ============ Helper robusti ============

def _extract_drive_id(url: str) -> str | None:
    """
    Estrae l'ID del file Google Drive da link nei formati più comuni:
    - https://drive.google.com/file/d/ID/view ...
    - https://drive.google.com/file/d/ID/preview
    - https://drive.google.com/open?id=ID
    - https://drive.google.com/uc?id=ID&export=download
    Ritorna None se non trova un ID valido.
    """
    if not url:
        return None
    url = url.strip()

    m = re.search(r"/file/d/([A-Za-z0-9_-]{10,})", url)
    if m:
        return m.group(1)

    m = re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url)
    if m:
        return m.group(1)

    return None


def _preview_url(file_id: str) -> str:
    """
    Costruisce il link embed PROFESSIONALE e corretto per l’iframe:
    https://drive.google.com/file/d/{file_id}/preview
    """
    file_id = (file_id or "").strip()
    return f"https://drive.google.com/file/d/{file_id}/preview"


# ============ Funzioni richieste ============

def registra_e_carica(id_partita: int) -> bool:
    """
    Registra il master, lo carica su Drive, genera link embed /preview,
    salva in 'video' e aggiorna 'calendario' (stato = FATTO).
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{ts}.mp4"
    path_locale = os.path.join(VIDEO_DIR, nome_file)

    # FFmpeg (profilo web-safe)
    cmd_ffmpeg = [
        'ffmpeg', '-y',
        '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30',
        '-vcodec', 'libx264', '-preset', 'veryfast',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        path_locale
    ]

    try:
        subprocess.run(cmd_ffmpeg, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Upload su Drive
        remote_path = f"{DRIVE_REMOTE}:{DRIVE_IN}/{nome_file}"
        subprocess.run([RCLONE_EXE, "copyto", path_locale, remote_path], check=True)

        # Link pubblico e conversione a /preview
        out = subprocess.run([RCLONE_EXE, "link", remote_path],
                             capture_output=True, text=True, check=True)
        link_raw = out.stdout.strip()
        file_id = _extract_drive_id(link_raw)
        if not file_id:
            raise RuntimeError(f"ID Drive non estratto dal link: {link_raw}")
        link_embed = _preview_url(file_id)

        # Salva DB
        supabase.table("video").insert({
            "nome_file": nome_file,
            "url_video": link_embed,
            "descrizione": f"Video partita {id_partita}"
        }).execute()

        supabase.table("calendario").update({
            "link_video": link_embed,
            "stato": "FATTO"
        }).eq("id", id_partita).execute()

        return True

    except Exception as e:
        print(f"[REGISTRA] Errore: {e}")
        try:
            supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        except:
            pass
        return False


def esegui_taglio_reale(id_partita: int, inizio: int, durata: int, id_richiesta: int) -> str | None:
    """
    Esegue il taglio clip, carica su Drive, ottiene link /preview e
    aggiorna la riga in comandi_clip (stato=COMPLETATO).
    Ritorna l’URL /preview o None in caso di errore.
    """
    # Trova il master locale più recente
    candidates = sorted(glob(os.path.join(VIDEO_DIR, f"match_{id_partita}_*.mp4")), reverse=True)
    if not candidates:
        print(f"[CLIP] Master non trovato per partita {id_partita}")
        return None
    master = candidates[0]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_clip = f"clip_{id_partita}_{id_richiesta}_{ts}.mp4"
    out_local = os.path.join(CLIP_DIR, nome_clip)

    # Taglio: tenta copia, poi fallback re-encode
    cmd_fast = ["ffmpeg","-y","-ss",str(inizio),"-i",master,"-t",str(durata),
                "-c","copy","-movflags","+faststart",out_local]
    cmd_safe = ["ffmpeg","-y","-ss",str(inizio),"-i",master,"-t",str(durata),
                "-c:v","libx264","-preset","veryfast","-crf","20",
                "-c:a","aac","-b:a","128k","-movflags","+faststart",out_local]

    try:
        try:
            subprocess.run(cmd_fast, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            subprocess.run(cmd_safe, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Upload clip
        remote_clip = f"{DRIVE_REMOTE}:{DRIVE_OUT}/{nome_clip}"
        subprocess.run([RCLONE_EXE, "copyto", out_local, remote_clip], check=True)

        # Link /preview
        out = subprocess.run([RCLONE_EXE, "link", remote_clip],
                             capture_output=True, text=True, check=True)
        link_raw = out.stdout.strip()
        file_id = _extract_drive_id(link_raw)
        if not file_id:
            raise RuntimeError(f"ID Drive non estratto dal link: {link_raw}")
        link_embed = _preview_url(file_id)

        # Aggiorna la richiesta
        supabase.table("comandi_clip").update({
            "url_video": link_embed,
            "stato": "COMPLETATO"
        }).eq("id", id_richiesta).execute()

        # Pulizia locale (facoltativa)
        try: os.remove(out_local)
        except: pass

        return link_embed

    except Exception as e:
        print(f"[CLIP] Errore taglio/upload: {e}")
        return None
