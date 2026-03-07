import sqlite3
import cv2
import os
import time
import subprocess
from datetime import datetime

# --- CONFIGURAZIONE ---
DB_PATH = "myplayr.db"
VIDEO_DIR = "ARCHIVIO_PARTITE"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita, nome_campo):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 AVVIO REGISTRAZIONE: {nome_file}...")
    
    # COMANDO FFmpeg (Cambia il nome della webcam se necessario)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_completo
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"✅ Registrazione completata: {nome_file}")
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
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Cerchiamo se c'è una partita programmata per ADESSO
            cursor.execute("SELECT id, campo FROM calendario WHERE data=? AND ora=? AND stato='PROGRAMMATO'", 
                           (data_oggi, ora_attuale))
            match = cursor.fetchone()
            
            if match:
                id_p, campo_p = match
                video_creato = registra_clip(id_p, campo_p)
                
                if video_creato:
                    # Aggiorniamo il database per dire che è FATTO
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
