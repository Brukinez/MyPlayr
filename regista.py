import os
import time
import subprocess
from datetime import datetime
from database import supabase  # Assicurati che database.py sia nella stessa cartella

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

    # COMANDO FFmpeg (30 secondi di test - verifica il nome della tua webcam!)
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
        # NOTA: Assicurati che "remote:CLIP_MYPLAYR" esista in Rclone
        subprocess.run([RCLONE_EXE, "copy", percorso_completo, "remote:CLIP_MYPLAYR"], check=True)
        
        # Step 3: Generazione Link Pubblico
        print(f"🔗 3. GENERAZIONE LINK PUBBLICO...")
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                                  capture_output=True, text=True, check=True)
        link_web = res_link.stdout.strip()

                # Step 4: TRASFORMAZIONE LINK E AGGIORNAMENTO SUPABASE
        # Puliamo il link di Drive per renderlo uno streaming diretto per l'app
        link_diretto = link_web.replace('/view?usp=drivesdk', '').replace('/view', '').replace('file/d/', 'uc?export=download&id=')
        
        supabase.table("calendario").update({
            "evento": nome_file, 
            "link_video": link_diretto, 
            "stato": "COMPLETATO" # Usiamo 'COMPLETATO' così l'app lo riconosce subito
        }).eq("id", id_partita).execute()
        
        print(f"🏁 PROCESSO FINITO: Match {id_partita} è online con link diretto!")
        return True

    except Exception as e:
        print(f"❌ ERRORE CRITICO DURANTE REGISTRAZIONE/UPLOAD: {e}")
        # Se fallisce, mettiamo lo stato a ERRORE per diagnostica
        supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        return False


def monitor():
    print("🚀 MOTORE MyPlayr LIVE ATTIVO. In ascolto su Supabase...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y")
            ora_attuale = now.strftime("%H:%M")
            
            # 🔎 CERCA MATCH DA INIZIARE ORA
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
                
                # CAMBIAMO SUBITO LO STATO per evitare che il loop lo trovi di nuovo mentre registra
                supabase.table("calendario").update({"stato": "REGISTRAZIONE"}).eq("id", id_p).execute()
                
                # Avviamo il processo (Registra -> Carica -> Link -> Fatto)
                registra_clip(id_p)
            else:
                # Debug silenzioso ogni 30 secondi
                print(f"😴 {ora_attuale} - Nessun match. Tutto tranquillo.")
            
        except Exception as e:
            print(f"⚠️ Errore di connessione o Database: {e}")
            
        time.sleep(30) # Controllo ogni 30 secondi

if __name__ == "__main__":
    monitor()

