import sqlite3
import subprocess
import time
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)


if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)

def registra_clip(id_partita, campo):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"match_{id_partita}_{timestamp}.mp4"
    full_path = os.path.join(VIDEO_DIR, filename)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '20', '-pix_fmt', 'yuv420p', full_path
    ]

    try:
        subprocess.run(command, check=True)
        return filename
    except Exception as e:
        print(f"Errore FFmpeg: {e}")
        return None

def monitor():
    while True:
        try:
            now = datetime.now()
            conn = sqlite3.connect("myplayr.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, campo FROM calendario WHERE data=? AND ora=? AND stato='PROGRAMMATO'", 
                           (now.strftime("%d-%m-%Y"), now.strftime("%H:%M")))
            match = cursor.fetchone()
            if match:
                res = registra_clip(match[0], match[1])
                if res:
                    cursor.execute("UPDATE calendario SET stato='FATTO', evento=? WHERE id=?", (res, match[0]))
                    conn.commit()
            conn.close()
        except: pass
        time.sleep(20)

if __name__ == "__main__": monitor()
