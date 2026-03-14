import os
import time
import subprocess
import sqlite3 # Lo teniamo per sicurezza ma usiamo Supabase
from datetime import datetime
from database import supabase # Carica il collegamento Cloud

# --- CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe" # Il tuo percorso Rclone

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 AVVIO REGISTRAZIONE LOCALE: {nome_file}...")

    # COMANDO FFmpeg (30 secondi di test)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_completo
    ]
    
    try:
        # 1. Registrazione Fisica
        subprocess.run(command, check=True)
        print(f"✅ Registrazione completata: {nome_file}")

        # 2. Caricamento su Google Drive (Rclone)
        print(f"🚀 Caricamento su Cloud in corso...")
        subprocess.run([RCLONE_EXE, "copy", percorso_completo, "remote:CLIP_MYPLAYR"], check=True)
        
        # 3. Generazione Link Pubblico
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                                  capture_output=True, text=True, check=True)
        link_web = res_link.stdout.strip()
        print(f"🌐 Link Cloud generato: {link_web}")

        # 4. Aggiornamento SUPABASE (Database Cloud)
        supabase.table("calendario").update({
            "evento": nome_file, 
            "link_video": link_web, 
            "stato": "FATTO"
        }).eq("id", id_partita).execute()
        
        print(f"✅ Database Cloud aggiornato per ID {id_partita}")
        return nome_file

    except Exception as e:
        print(f"❌ Errore durante il processo: {e}")
        return None

def monitor():
    print("🚀 Motore MyPlayr LIVE (Supabase) ATTIVO. In attesa...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")
            
            print(f"🕒 Orario PC: {ora_attuale} | Cerco match su Supabase...")

            # Chiediamo a Supabase se c'è un match ORA
            response = supabase.table("calendario")\
                .select("*")\
                .eq("data", data_oggi)\
                .eq("ora", ora_attuale)\
                .eq("stato", "PROGRAMMATO")\
                .execute()
            
            match_list = response.data

            if match_list:
                # Se troviamo almeno un match (prendiamo il primo)
                match = match_list[0]
                id_p = match['id']
                print(f"🎬 MATCH TROVATO! ID: {id_p} - Avvio registrazione...")
                
                registra_clip(id_p)
                print(f"💾 Ciclo completato per ID {id_p}")
            else:
                # Se non c'è nulla, facciamo lo "spionaggio" per vedere cosa c'è nel Cloud
                print(f"🕒 {ora_attuale} - Nessun match programmato.")
                # Opzionale: stampa tutto quello che c'è nel Cloud per debug
                res_all = supabase.table("calendario").select("id, data, ora, stato").limit(5).execute()
                print(f"📊 Ultime righe nel Cloud: {res_all.data}")
            
        except Exception as e:
            print(f"⚠️ Errore connessione Cloud: {e}")
            
        time.sleep(30) # Controlla ogni 30 secondi

if __name__ == "__main__":
    monitor()
