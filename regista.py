import os
import time
import subprocess
from datetime import datetime
from database import supabase  # Assicuratevi che database.py sia nella stessa cartella

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
    
    print(f"🔴 1. AVVIO REGISTRAZIONE FISICA: {nome_file}...")

    # COMANDO FFmpeg (30 secondi di test)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_completo
    ]
    
    try:
        # Step 1: Registrazione
        subprocess.run(command, check=True)
        print(f"✅ Registrazione completata localmente.")

        # Step 2: Caricamento su Google Drive
        print(f"🚀 2. CARICAMENTO SU CLOUD...")
        subprocess.run([RCLONE_EXE, "copy", percorso_completo, "remote:CLIP_MYPLAYR"], check=True)
        
        # Step 3: Generazione Link Pubblico
        print(f"🔗 3. GENERAZIONE LINK PUBBLICO...")
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                                  capture_output=True, text=True, check=True)
        link_web = res_link.stdout.strip()

        # Step 4: TRASFORMAZIONE LINK PER STREAMING DIRETTO
        # Trasformiamo il link di Drive in un formato che il sito può "leggere" come video
        link_diretto = link_web.replace('/view?usp=drivesdk', '').replace('/view', '').replace('file/d/', 'uc?export=download&id=')
        
        # --- NUOVA PARTE: SCRITTURA NELLA TABELLA VIDEO ---
        print(f"💾 4. SALVATAGGIO NEL DATABASE...")
        
        # Inseriamo il video nella tabella 'video' (quella che leggerà il sito)
        supabase.table("video").insert({
            "nome_file": nome_file,
            "url_video": link_diretto,
            "descrizione": f"Registrazione Match ID {id_partita}"
        }).execute()

        # Aggiorniamo anche il calendario per dire che è 'FATTO'
        supabase.table("calendario").update({
            "evento": nome_file, 
            "link_video": link_diretto, 
            "stato": "FATTO" 
        }).eq("id", id_partita).execute()
        
        print(f"🏁 PROCESSO FINITO: Video salvato e Match {id_partita} online!")
        return True

    except Exception as e:
        print(f"❌ ERRORE CRITICO: {e}")
        supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        return False

def monitor():
    print("🚀 MOTORE MyPlayr LIVE ATTIVO. In ascolto su Supabase...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y") # Assicurati che il formato sia uguale a Supabase
            ora_attuale = now.strftime("%H:%M")
            
            response = supabase.table("calendario")\
                .select("*")\
                .eq("data", data_oggi)\
                .eq("ora", ora_attuale)\
                .eq("stato", "PROGRAMMATO")\
                .execute()
            
            match_list = response.data

            if match_list:
                match = match_list[0]
                id_p = match['id']
                print(f"🎬 MATCH TROVATO! ID: {id_p} - Ore: {ora_attuale}")
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", id_p).execute()
                registra_clip(id_p)
            else:
                print(f"😴 {ora_attuale} - Nessun match in programma ora.")
            
        except Exception as e:
            print(f"⚠️ Errore: {e}")
            
        time.sleep(30)

if __name__ == "__main__":
    monitor()
