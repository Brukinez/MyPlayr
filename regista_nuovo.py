import os
import re
import time
import subprocess
import json
from glob import glob
from datetime import datetime
from database import supabase

# ============ CONFIGURAZIONE (Sincronizzata con Claude) ============
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR       = os.getenv("VIDEO_DIR", os.path.join(BASE_DIR, "ARCHIVIO_PARTITE"))
CLIP_DIR        = os.getenv("CLIP_DIR",  os.path.join(BASE_DIR, "CLIP_TAGLIATE"))
RCLONE_EXE      = r"C:\MyPlayr\Rclone\rclone.exe" # Percorso fisso come tuo originale
DRIVE_REMOTE    = "remote"
DRIVE_IN        = "CLIP_MYPLAYR"
DRIVE_OUT       = "CLIP_MYPLAYR/CLIPS" # Cartella specifica per le clip su Drive

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(CLIP_DIR,  exist_ok=True)

# ============ HELPER FUNCTIONS ============
def _estrai_id(link: str):
    if not link: return None
    m = re.search(r"/file/d/([A-Za-z0-9_-]+)", link) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", link)
    return m.group(1) if m else None

def _preview_url(fid: str):
    return f"https://google.com{fid}/preview"

def _rclone_link(path_remote: str):
    out = subprocess.run([RCLONE_EXE, "link", path_remote], capture_output=True, text=True, check=True)
    return out.stdout.strip()

def _trova_master_locale(id_partita: int):
    # Cerca file che iniziano con match_ID_
    files = sorted(glob(os.path.join(VIDEO_DIR, f"match_{id_partita}_*.mp4")), reverse=True)
    return files[0] if files else None

def _scarica_master_da_drive(id_partita: int):
    print(f"☁️ Master non trovato in locale. Cerco su Drive per partita {id_partita}...")
    out = subprocess.run([RCLONE_EXE, "lsjson", f"{DRIVE_REMOTE}:{DRIVE_IN}"],
                         capture_output=True, text=True, check=True).stdout
    try:
        listing = json.loads(out)
    except:
        return None
    candidati = [f["Name"] for f in listing if f.get("Name","").startswith(f"match_{id_partita}_") and f["Name"].endswith(".mp4")]
    if not candidati: return None
    nome = sorted(candidati, reverse=True)[0]
    src = f"{DRIVE_REMOTE}:{DRIVE_IN}/{nome}"
    dst = os.path.join(VIDEO_DIR, nome)
    subprocess.run([RCLONE_EXE, "copyto", src, dst], check=True)
    return dst if os.path.exists(dst) else None

# ============ CORE LOGIC ============
def esegui_taglio_reale(id_partita, inizio, durata, id_richiesta):
    master = _trova_master_locale(id_partita) or _scarica_master_da_drive(id_partita)
    if not master:
        print(f"❌ [TAGLIO] Master non trovato per partita {id_partita}")
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_clip = f"clip_{id_partita}_{id_richiesta}_{ts}.mp4"
    out_local = os.path.join(CLIP_DIR, nome_clip)

    # Taglio: tenta veloce, poi fallback sicuro
    print(f"✂️ Taglio in corso: {nome_clip}...")
    cmd_fast = [ "ffmpeg","-y","-ss",str(inizio),"-i",master,"-t",str(durata),"-c","copy","-movflags","+faststart",out_local ]
    
    try:
        subprocess.run(cmd_fast, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("⚠️ Taglio veloce fallito, provo re-encoding...")
        cmd_safe = ["ffmpeg","-y","-ss",str(inizio),"-i",master,"-t",str(durata),"-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","128k","-movflags","+faststart",out_local]
        subprocess.run(cmd_safe, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Upload e Link
    remote_path = f"{DRIVE_REMOTE}:{DRIVE_OUT}/{nome_clip}"
    subprocess.run([RCLONE_EXE, "copyto", out_local, remote_path], check=True)

    link = _rclone_link(remote_path)
    fid  = _estrai_id(link)
    if not fid: return None
    url_preview = _preview_url(fid)

    # Aggiorna DB
    supabase.table("comandi_clip").update({"url_video": url_preview, "stato": "COMPLETATO"}).eq("id", id_richiesta).execute()

    if os.path.exists(out_local): os.remove(out_local)
    return url_preview

def elabora_taglio_clip():
    try:
        res = supabase.table("comandi_clip").select("*").eq("stato","RICHIESTO").order("id", desc=True).limit(5).execute()
        for r in (res.data or []):
            print(f"🔔 Nuova richiesta: Match {r['id_partita']} @ {r['inizio_secondi']}s")
            esegui_taglio_reale(int(r["id_partita"]), int(r["inizio_secondi"]), int(r["durata_secondi"]), int(r["id"]))
    except Exception as e:
        print(f"❌ Errore fetch richieste: {e}")

def registra_e_carica(id_partita):
    # Ripresa la tua funzione originale per non cambiare il setup hardware
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    path_locale = os.path.join(VIDEO_DIR, nome_file)
    
    command = ['ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam', '-t', '30', '-vcodec', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path_locale]

    try:
        subprocess.run(command, check=True)
        subprocess.run([RCLONE_EXE, "copy", path_locale, f"{DRIVE_REMOTE}:{DRIVE_IN}"], check=True)
        link_drive = _rclone_link(f"{DRIVE_REMOTE}:{DRIVE_IN}/{nome_file}")
        fid = _estrai_id(link_drive)
        url_p = _preview_url(fid)

        supabase.table("video").insert({"nome_file": nome_file, "url_video": url_p, "descrizione": f"Video partita {id_partita}"}).execute()
        supabase.table("calendario").update({"link_video": url_p, "stato": "FATTO"}).eq("id", id_partita).execute()
        print(f"✅ Match {id_partita} caricato!")
        return True
    except Exception as e:
        print(f"❌ Errore registrazione: {e}")
        return False

# ============ MONITOR LOOP ============
def monitor():
    print(f"🚀 BRUKINEZ REGISTA (NUOVO) - Monitor attivo su {VIDEO_DIR}")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")

            # A. Controllo Match
            resp = supabase.table("calendario").select("*").eq("data", data_oggi).eq("ora", ora_attuale).eq("stato", "PROGRAMMATO").execute()
            if resp.data:
                p = resp.data[0]
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", p['id']).execute()
                registra_e_carica(p['id'])
            
            # B. Controllo Tagli
            elabora_taglio_clip()

        except Exception as err:
            print(f"⚠️ Errore loop: {err}")
        
        time.sleep(15)

if __name__ == "__main__":
    monitor()
