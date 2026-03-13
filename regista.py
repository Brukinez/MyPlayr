import sqlite3
import os
import time
import subprocess
from datetime import datetime

# --- CONFIGURAZIONE ---
DB_PATH = "myplayr_finale.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Cartella locale dove FFmpeg salva inizialmente (assicurati che esista)
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
# Percorso del motore Rclone che abbiamo configurato
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_fisico = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 AVVIO REGISTRAZIONE LOCALE: {nome_file}...")

    # COMANDO FFmpeg (30 secondi di test)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_fisico
    ]
    
    try:
        # 1. Registrazione Fisica
        subprocess.run(command, check=True)
        print(f"✅ Registrazione salvata in locale: {nome_file}")

        # 2. Caricamento su Google Drive (Rclone)
        print(f"🚀 Caricamento su Cloud in corso...")
        subprocess.run([RCLONE_EXE, "copy", percorso_fisico, "remote:CLIP_MYPLAYR"], check=True)
        
        # 3. Generazione Link Pubblico
        res = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                             capture_output=True, text=True, check=True)
        link_web = res.stdout.strip()
        print(f"🌐 Link Cloud generato: {link_web}")

        # 4. Aggiornamento Database Locale
        conn = sqlite3.connect(DB_PATH)
        # Salviamo nome file, link cloud e stato FATTO
        conn.execute("UPDATE calendario SET evento=?, link_video=?, stato='FATTO' WHERE id=?", 
                     (nome_file, link_web, id_partita))
        conn.commit()
        conn.close()
        
        return nome_file
    except Exception as e:
        print(f"❌ Errore durante il processo: {e}")
        return None

def monitor():
    print("🚀 Motore MyPlayr ATTIVO. In attesa di partite...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Cerca partite PROGRAMMATE per l'ora esatta
            cursor.execute("SELECT id FROM calendario WHERE data=? AND ora=? AND stato='PROGRAMMATO'", 
                           (data_oggi, ora_attuale))
            match = cursor.fetchone()
            
            if match:
                id_p = match[0]
                registra_clip(id_p)
                print(f"💾 Ciclo completato per ID {id_p}")
            else:
                print(f"🕒 {ora_attuale} - Nessun match programmato.")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Errore ciclo: {e}")
            
        time.sleep(30) # Controlla ogni 30 secondi

if __name__ == "__main__":
    monitor()
