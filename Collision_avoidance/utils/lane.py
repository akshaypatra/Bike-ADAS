import cv2
import numpy as np

def region_of_interest(img):
    height = img.shape[0]
    polygons = np.array([[
        (0, height),
        (img.shape[1], height),
        (img.shape[1], int(height*0.6)),
        (0, int(height*0.6))
    ]])
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, polygons, 255)
    return cv2.bitwise_and(img, mask)

def draw_lines(img, lines):
    if lines is None:
        return img

    for line in lines:
        x1,y1,x2,y2 = line.reshape(4)
        cv2.line(img,(x1,y1),(x2,y2),(255,0,0),5)
    return img

def detect_lanes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5,5),0)

    edges = cv2.Canny(blur,50,150)

    cropped = region_of_interest(edges)

    lines = cv2.HoughLinesP(
        cropped,
        rho=2,
        theta=np.pi/180,
        threshold=100,
        minLineLength=40,
        maxLineGap=5
    )

    lane_image = frame.copy()
    lane_image = draw_lines(lane_image, lines)

    return lane_image
