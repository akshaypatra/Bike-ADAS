KNOWN_CAR_HEIGHT = 1.5   # meters
FOCAL_LENGTH = 700      # tweak for your camera/video

def estimate_distance(box_height):
    if box_height <= 0:
        return 999
    return (KNOWN_CAR_HEIGHT * FOCAL_LENGTH) / box_height
