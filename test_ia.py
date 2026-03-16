import cv2
from ultralytics import YOLO

# 1. Carichiamo l'IA specifica per lo sport
model = YOLO('yolov8n.pt') 
cap = cv2.VideoCapture(0) 

# --- MEMORIA PER MYPLAYR ---
palla_in_campo = False

print("⚽ SIMULAZIONE PARTITA: Cerco Giocatori (0) e Palla (32)")

while True:
    ret, frame = cap.read()
    if not ret: break

    # ORA I NUMERI SONO DENTRO LE PARENTESI: [0, 32]
    results = model.track(frame, persist=True, classes=[0, 32], verbose=False) 

    # Prendiamo il primo risultato
    res = results[0]
    ora_vedo_palla = False
    ora_vedo_giocatore = False

    # Controlliamo cosa vede l'IA in questo istante
    if res.boxes:
        for box in res.boxes:
            classe = int(box.cls)
            if classe == 32: ora_vedo_palla = True
            if classe == 0: ora_vedo_giocatore = True

    # --- LOGICA HIGHLIGHT ---
    # Disegniamo il risultato sul video
    annotated_frame = res.plot() 
    
    # Se ci sei TU + LA PALLA, scatta l'azione!
    if ora_vedo_palla and ora_vedo_giocatore:
        if not palla_in_campo:
            print("🌟 [HIGHLIGHT] Azione rilevata! Segno il minuto sul database...")
            palla_in_campo = True
        
        # Scriviamo "REGISTRAZIONE" bello grande in VERDE sul video
        cv2.putText(annotated_frame, "REGISTRAZIONE ATTIVA", (50, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    else:
        palla_in_campo = False

    cv2.imshow("MyPlayr AI - Campo di Gioco", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
