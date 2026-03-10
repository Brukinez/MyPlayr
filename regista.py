import sqlite3
import os
import time
import subprocess
from datetime import datetime

# --- CONFIGURAZIONE ---
DB_PATH = "myplayr_v3.db"
# Il percorso verso il tuo Google Drive
VIDEO_DIR = r"G:\Il mio Drive\CLIP_MYPLAYR"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    
    # QUESTA È LA RIGA CRUCIALE: deve esserci VIDEO_DIR (quello di G:)
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 AVVIO REGISTRAZIONE SU GOOGLE DRIVE: {nome_file}...")

    
    # COMANDO FFmpeg (Webcam del tuo PC)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_completo
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"✅ Registrazione salvata in G: {nome_file}")
        return nome_file
    except Exception as e:
        print(f"❌ Errore FFmpeg: {e}")
        return None

def monitor():
    print("🚀 Motore MyPlayr ATTIVO. In attesa di partite...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")
            print(f"Orario PC attuale: {now.strftime('%H:%M')} | Cerco partita alle: {ora_attuale}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
                        # --- RIGA DI TEST PER VEDERE COSA C'È NEL DB ---
            cursor.execute("SELECT COUNT(*) FROM calendario WHERE stato='PROGRAMMATO'")
            quante_partite = cursor.fetchone()[0]
            print(f"📡 Partite in attesa nel database locale: {quante_partite}")

               # --- CREA TABELLA SE MANCA ---
            cursor.execute('''CREATE TABLE IF NOT EXISTS calendario 
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                               data TEXT, ora TEXT, campo TEXT, 
                               stato TEXT, evento TEXT)''')
            conn.commit()
         
            # Cerca partite PROGRAMMATE per l'ora esatta
            cursor.execute("SELECT id FROM calendario WHERE data=? AND ora=? AND stato='PROGRAMMATO'", 
                           (data_oggi, ora_attuale))
            match = cursor.fetchone()
            
            if match:
                id_p = match[0]
                video_creato = registra_clip(id_p)
                
                if video_creato:
                    cursor.execute("UPDATE calendario SET stato='FATTO', evento=? WHERE id=?", 
                                   (video_creato, id_p))
                    conn.commit()
                    print(f"💾 Database aggiornato per ID {id_p}")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Errore ciclo: {e}")
            
        time.sleep(30) # Controlla ogni 30 secondi

if __name__ == "__main__":
    monitor()
