from ultralytics import YOLO
import cv2

# Load YOLOv8 pretrained model
model = YOLO("yolov8n.pt")  


cap = cv2.VideoCapture("./videos/RearCameraFootage2.mov")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)  # Run detection

    # Initialize alert priority variables for this frame
    highest_priority = 0  # 0 = no alert, 1 = Vehicle detected, 2 = Closing vehicle, 3 = VEHICLE ALERT!
    alert_color = None
    alert_text = ""

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label in ["car", "motorbike", "truck", "bus"]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                bbox_height = y2 - y1  # Approximation of distance

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Determine alert priority
                if bbox_height > 300 and highest_priority < 3:
                    highest_priority = 3
                    alert_text = "VEHICLE ALERT!"
                    alert_color = (0, 0, 255)  # Red
                elif bbox_height > 150 and highest_priority < 2:
                    highest_priority = 2
                    alert_text = "CLOSING VEHICLE"
                    alert_color = (0, 255, 255)  # Yellow
                elif bbox_height > 70 and highest_priority < 1:
                    highest_priority = 1
                    alert_text = "Vehicle detected"
                    alert_color = (0, 255, 0)  # Green

    # Draw the highest priority alert per frame
    if alert_text:
        cv2.putText(frame, alert_text, (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, alert_color, 3)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
