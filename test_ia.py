import cv2
from ultralytics import YOLO

# Diciamo al computer di usare un'IA "piccola" così non fa troppa fatica
model = YOLO('yolov8n.pt') 

# Accendiamo la tua webcam
cap = cv2.VideoCapture(0) 

print("Sto accendendo la webcam... alzati e preparati!")

while True:
    # Il computer scatta una foto velocissima (frame)
    ret, frame = cap.read()
    if not ret:
        break

    # L'IA cerca se c'è una PERSONA nella foto
    results = model.track(frame, persist=True, classes=[0, 39]) 

    # Disegna un quadrato colorato attorno a te
    annotated_frame = results[0].plot() 

    # Mostra il risultato in una finestrella
    cv2.imshow("Il mio primo test IA", annotated_frame)

    # Se premi il tasto 'q' sulla tastiera, il programma si ferma
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Spegniamo tutto correttamente
cap.release()
cv2.destroyAllWindows()
