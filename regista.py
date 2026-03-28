import os
import time
import subprocess
import re
from datetime import datetime
from database import supabase  # Assicurati che database.py sia nella stessa cartella

# --- CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "ARCHIVIO_PARTITE")
RCLONE_EXE = r"C:\MyPlayr\Rclone\rclone.exe" # Percorso assoluto rclone.exe

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def registra_clip(id_partita):
    """Esegue la registrazione FFmpeg, carica su Drive e aggiorna Supabase."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"match_{id_partita}_{timestamp}.mp4"
    percorso_completo = os.path.join(VIDEO_DIR, nome_file)
    
    print(f"🔴 1. AVVIO REGISTRAZIONE FISICA: {nome_file}...")

    # COMANDO FFmpeg (30 secondi di test - Adatta il nome della webcam se necessario)
    command = [
        'ffmpeg', '-y', '-f', 'dshow', '-i', 'video=USB2.0 VGA UVC WebCam',
        '-t', '30', '-pix_fmt', 'yuv420p', percorso_completo
    ]
    
    try:
        # Step 1: Registrazione fisica
        subprocess.run(command, check=True)
        print(f"✅ Registrazione completata localmente in: {percorso_completo}")

        # Step 2: Caricamento su Google Drive tramite Rclone
        print(f"🚀 2. CARICAMENTO SU CLOUD (Google Drive)...")
        subprocess.run([RCLONE_EXE, "copy", percorso_completo, "remote:CLIP_MYPLAYR"], check=True)
        
        # Step 3: Recupero Link da Drive
        print(f"🔗 3. GENERAZIONE LINK PUBBLICO...")
        res_link = subprocess.run([RCLONE_EXE, "link", f"remote:CLIP_MYPLAYR/{nome_file}"], 
                                  capture_output=True, text=True, check=True)
        link_web = res_link.stdout.strip()

        # Step 4: Trasformazione Link per Streaming e Aggiornamento Finale
        print(f"🔗 4. PULIZIA LINK PER STREAMING E CHIUSURA...")
        
        # Estraiamo l'ID univoco di Google Drive per creare il link di download diretto
        match_id_drive = re.search(r"([a-zA-Z0-9_-]{25,})", link_web)
        
        if match_id_drive:
            id_puro = match_id_drive.group(1)
            link_diretto = f"https://drive.google.com{id_puro}"
        else:
            link_diretto = link_web # Fallback se la regex non trova l'ID

        # Aggiorniamo Supabase: Stato passa a FATTO e inseriamo il link pulito
        supabase.table("calendario").update({
            "evento": nome_file, 
            "link_video": link_diretto, 
            "stato": "FATTO" 
        }).eq("id", id_partita).execute()
        
        print(f"🏁 PROCESSO FINITO: Match {id_partita} è ora online e visibile nell'app!")
        return True

    except Exception as e:
        print(f"❌ ERRORE CRITICO DURANTE IL PROCESSO: {e}")
        # In caso di errore, marchiamo il match così l'admin può resettarlo
        supabase.table("calendario").update({"stato": "ERRORE"}).eq("id", id_partita).execute()
        return False


def monitor():
    """Resta in ascolto di nuovi match programmati su Supabase."""
    print("🚀 MOTORE MyPlayr LIVE ATTIVO. In ascolto su Supabase...")
    while True:
        try:
            now = datetime.now()
            data_oggi = now.strftime("%d-%m-%Y") # Assicurati che il formato su Supabase sia GG-MM-AAAA
            ora_attuale = now.strftime("%H:%M")
            
            # Cerchiamo match programmati per l'ora esatta di oggi
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
                
                # CAMBIAMO SUBITO LO STATO per evitare che il loop trovi lo stesso match nel prossimo ciclo di 30s
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
