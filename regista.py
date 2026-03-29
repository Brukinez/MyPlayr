import os
import time
import subprocess
import re
from datetime import datetime
from database import supabase 

# --- CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe" 

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 1. AVVIO REGISTRAZIONE FISICA: {nome_file}...")

    # COMANDO FFMPEG (DEFINITO PRIMA DI TRY)
        # --- 1. REGISTRAZIONE FISICA ---
    # Abbiamo aggiunto '-c:v libx264' e '-movflags +faststart' per far vedere il video subito online
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-movflags', '+faststart', 
        percorso_completo
    ]
    
    try:
        subprocess.run(command, check=True)
        
        # --- 2. CARICAMENTO SU GOOGLE DRIVE ---
        subprocess.run([RCLONE_EXE, "copy", percorso_completo, "remote:CLIP_MYPLAYR"], check=True)
        
        # --- 3. PRENDIAMO IL LINK DA GOOGLE DRIVE ---
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                                  capture_output=True, text=True, check=True)
        link_web = res_link.stdout.strip()

        # --- 4. SISTEMIAMO IL LINK PER IL SITO (Fondamentale!) ---
        match_id = re.search(r"([a-zA-Z0-9_-]{25,})", link_web)
        if match_id:
            id_puro = match_id.group(1)
            # Creiamo un link speciale che finisce con /preview
            link_diretto = f"https://drive.google.com{id_puro}/preview"
        else:
            link_diretto = link_web

        # Scriviamo il link corretto su Supabase
        supabase.table("calendario").update({
            "link_video": link_diretto, 
            "stato": "FATTO" 
        }).eq("id", id_partita).execute()
        
        return True


    except Exception as e:
        print(f"❌ ERRORE CRITICO DURANTE REGISTRAZIONE/UPLOAD: {e}")
        supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        return False

def monitor():
    print("🚀 MOTORE MyPlayr LIVE ATTIVO. In ascolto su Supabase...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%Y-%m-%d") 
            ora_attuale = now.strftime("%H:%M")
            
            response = supabase.table("calendario")\
                .select("*")\
                .eq("data", data_oggi)\
                .eq("ora", ora_attuale)\
                .eq("stato", "PROGRAMMATO")\
                .execute()
            
            match_list = response.data

            if match_list:
                # Prendiamo il primo match della lista (indice 0)
                match = match_list[0]
                id_p = match['id']
                
                print(f"🎬 MATCH TROVATO! ID: {id_p} - Ore: {ora_attuale}")
                
                # CAMBIAMO SUBITO LO STATO per evitare che il loop lo trovi lo stesso match nel prossimo ciclo di 30s
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", id_p).execute()
                
                # Avviamo la sequenza di registrazione e upload
                registra_clip(id_p)
                
            else:
                # Debug a console per sapere che il sistema è vivo
                print(f"😴 {ora_attuale} - Nessun match programmato ora. Controllo tra 30s...")
            
        except Exception as e:
            print(f"⚠️ Errore di connessione o Database: {e}")
            
        time.sleep(30) # Intervallo di polling

if __name__ == "__main__":
    monitor()

