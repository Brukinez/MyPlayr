import os, re, time, subprocess, json
from glob import glob
from datetime import datetime
from database import supabase

# ============ CONFIGURAZIONE HARDWARE (PERCORSI FISSI) ============
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR       = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
CLIP_DIR        = os.path.join(BASE_DIR, "CLIP_TAGLIATE")
RCLONE_EXE      = r"C:\MyPlayr\Rclone\rclone.exe" 
DRIVE_REMOTE    = "remote"
DRIVE_IN        = "CLIP_MYPLAYR"
DRIVE_OUT       = "CLIP_MYPLAYR/CLIPS"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(CLIP_DIR,  exist_ok=True)

# ============ HELPER: FIX LINK GOOGLE DRIVE ============
def _extract_drive_id(url: str):
    if not url: return None
    url = url.strip()
    # Estrazione robusta dell'ID
    m = re.search(r"/file/d/([A-Za-z0-9_-]{10,})", url) or re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url)
    return m.group(1) if m else None

def _preview_url(file_id: str):
    # IL LINK CORRETTO PER IL SITO
    return f"https://google.com{file_id}/preview"

def _rclone_link(path_remote: str):
    out = subprocess.run([RCLONE_EXE, "link", path_remote], capture_output=True, text=True, check=True)
    return out.stdout.strip()

# ============ CORE: REGISTRAZIONE E TAGLIO ============
def registra_e_carica(id_partita):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{ts}.mp4"
    path_locale = os.path.join(VIDEO_DIR, nome_file)
    print(f"🎥 Avvio registrazione match {id_partita}...")
    cmd = ['ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam', '-t', '30', '-vcodec', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path_locale]
    try:
        subprocess.run(cmd, check=True)
        print("☁️ Caricamento match su Drive...")
        subprocess.run([RCLONE_EXE, "copy", path_locale, f"{DRIVE_REMOTE}:{DRIVE_IN}"], check=True)
        link_raw = _rclone_link(f"{DRIVE_REMOTE}:{DRIVE_IN}/{nome_file}")
        fid = _extract_drive_id(link_raw)
        link_embed = _preview_url(fid)
        supabase.table("video").insert({"nome_file": nome_file, "url_video": link_embed, "descrizione": f"Match {id_partita}"}).execute()
        supabase.table("calendario").update({"link_video": link_embed, "stato": "FATTO"}).eq("id", id_partita).execute()
        print(f"✅ Match {id_partita} completato!")
    except Exception as e: print(f"❌ Errore match: {e}")

def esegui_taglio_reale(id_partita, inizio, durata, id_richiesta):
    print(f"✂️ Cerco master per match {id_partita}...")
    candidates = sorted(glob(os.path.join(VIDEO_DIR, f"match_{id_partita}_*.mp4")), reverse=True)
    if not candidates: 
        print(f"❌ Master non trovato locale.")
        return None
    master = candidates[0]
    nome_clip = f"clip_{id_richiesta}.mp4"
    out_local = os.path.join(CLIP_DIR, nome_clip)
    print(f"🎬 Taglio in corso...")
    cmd = ["ffmpeg","-y","-ss",str(inizio),"-i",master,"-t",str(durata),"-c","copy","-movflags","+faststart",out_local]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        remote_clip = f"{DRIVE_REMOTE}:{DRIVE_OUT}/{nome_clip}"
        subprocess.run([RCLONE_EXE, "copyto", out_local, remote_clip], check=True)
        link_raw = _rclone_link(remote_clip)
        fid = _extract_drive_id(link_raw)
        link_embed = _preview_url(fid)
        supabase.table("comandi_clip").update({"url_video": link_embed, "stato": "COMPLETATO"}).eq("id", id_richiesta).execute()
        if os.path.exists(out_local): os.remove(out_local)
        print(f"✅ Clip {id_richiesta} COMPLETATA!")
        return link_embed
    except Exception as e:
        print(f"❌ Errore taglio: {e}")
        return None

# ============ MONITOR ============
def elabora_taglio_clip():
    try:
        res = supabase.table("comandi_clip").select("*").eq("stato","RICHIESTO").execute()
        for r in (res.data or []):
            esegui_taglio_reale(int(r["id_partita"]), int(r["inizio_secondi"]), int(r["durata_secondi"]), int(r["id"]))
    except Exception as e: print(f"❌ Errore fetch: {e}")

def monitor():
    print(f"🚀 BRUKINEZ REGISTA ATTIVO (Fix Link Drive)")
    while True:
        try:
            # A. Controllo Match Programmatori
            now = datetime.now()
            resp = supabase.table("calendario").select("*").eq("data", now.strftime("%d-%m-%Y")).eq("ora", now.strftime("%H:%M")).eq("stato", "PROGRAMMATO").execute()
            if resp.data:
                for p in resp.data:
                    supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", p['id']).execute()
                    registra_e_carica(p['id'])
            # B. Controllo Tagli
            elabora_taglio_clip()
        except Exception as err: print(f"⚠️ Errore loop: {err}")
        time.sleep(15)

if __name__ == "__main__":
    monitor()
