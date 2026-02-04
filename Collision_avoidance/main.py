import cv2
from ultralytics import YOLO
from tracker.centroid_tracker import CentroidTracker
from utils.distance import estimate_distance
from utils.lane import detect_lanes

model = YOLO("models/yolov8n.pt")
cap = cv2.VideoCapture("data/traffic.mp4")

tracker = CentroidTracker()
prev_distance = {}

FPS = cap.get(cv2.CAP_PROP_FPS)
if FPS == 0:
    FPS = 30

while True:
    ret, frame = cap.read()
    if not ret:
        break

    H, W, _ = frame.shape

    # Lane Detection
    frame = detect_lanes(frame)

    # Ego vehicle reference line (center horizontal)
    ego_line = int(H * 0.55)
    cv2.line(frame, (0, ego_line), (W, ego_line), (255,255,255), 2)

    results = model(frame)[0]

    rects = []

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls in [2,3,5,7]:
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            rects.append((x1,y1,x2,y2))

    objects = tracker.update(rects)

    for ((x1,y1,x2,y2), objectID) in zip(rects, objects.keys()):

        h = y2 - y1
        cy = int((y1+y2)/2)

        distance = estimate_distance(h)

        if objectID in prev_distance:
            speed = (prev_distance[objectID] - distance) * FPS
        else:
            speed = 0

        prev_distance[objectID] = distance

        if speed != 0:
            ttc = abs(distance / speed)
        else:
            ttc = 999

        # FRONT OR REAR?
        position = "FRONT" if cy < ego_line else "REAR"

        color = (0,255,0)

        # ---------- FRONT COLLISION ----------
        if position == "FRONT" and speed > 0 and ttc < 2:
            cv2.putText(frame,"FRONT COLLISION WARNING",
                        (40,80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,(0,0,255),3)
            color = (0,0,255)

        # ---------- REAR COLLISION ----------
        if position == "REAR" and speed < 0 and ttc < 2:
            cv2.putText(frame,"REAR COLLISION WARNING",
                        (40,120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,(0,0,255),3)
            color = (0,0,255)

        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)

        cv2.putText(frame,
                    f"ID:{objectID} {position} {distance:.1f}m",
                    (x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,(255,255,0),2)

    cv2.imshow("ADAS Forward + Rear Collision System", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
