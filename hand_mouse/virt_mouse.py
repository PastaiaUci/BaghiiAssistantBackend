import cv2
import time
import numpy as np
from hand_track_module import HandDetector
import pyautogui as autopy

# Set width and height of window
wCam, hCam = 640, 480
frameR = 100  # Frame reduction
smoothening = 5
plocx, plocy = 0, 0
clocx, clocy = 0, 0

# Set pTime
pTime = 0

# Set camera and dimensions
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Try using DirectShow backend
cap.set(3, wCam)
cap.set(4, hCam)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Initialize Hand detector
detector = HandDetector(maxHands=1)

wScr, hScr = autopy.size()

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture image")
        continue

    if img is None:
        print("Error: img is None")
        continue

    img = cv2.flip(img, 1)  # Original solution to flip whole image
    
    # Get hand landmarks
    try:
        img = detector.getHands(img)
    except Exception as e:
        print(f"Error in getHands: {e}")
        continue

    lmlist, bbox = detector.getPos(img, draw=False)
    
    # Print landmark list for debugging
    print(f"LmList: {lmlist}")
    
    # We will need the tip of the index and middle finger
    if len(lmlist) != 0:
        x1, y1 = lmlist[8][1:]  # Index finger 
        x2, y2 = lmlist[12][1:]  # Middle finger 

        # Check what fingers are up
        fingers = detector.fingersUp()
        print(f"Fingers: {fingers}")

        cv2.rectangle(img, (frameR, frameR), (wCam-frameR, hCam-frameR), (255, 0, 255), 2)

        # Only index finger is moving mode
        if fingers[1] == 1 and fingers[2] == 0:
            # Convert coordinates and smooth values
            x3 = np.interp(x1, (frameR, wCam-frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam-frameR), (0, hScr))

            # Smoothening
            clocx = plocx + (x3 - plocx)/smoothening
            clocy = plocy + (y3 - plocy)/smoothening

            # Print smoothened coordinates for debugging
            print(f"Smoothened Coordinates: ({clocx}, {clocy})")

            # Move mouse
            autopy.moveTo(clocx, clocy)  # This work if whole image flipped
            # autopy.moveTo(wScr-x3, y3)  # This works if whole image is NOT flipped

            plocx, plocy = clocx, clocy

        # Both fingers is click mode
        if fingers[1] == 1 and fingers[2] == 1:
            # Find distance between fingers
            length, img = detector.findDistance(8, 12, img)
            # If short dist then click
            if length < 35:
                cv2.circle(img, (x1, y1), 4, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (x2, y2), 4, (0, 255, 0), cv2.FILLED)
                autopy.click()

    # Adding frame rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)

    # Display
    cv2.imshow("Image", img)
    # Check for 'q' key to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close any OpenCV windows
cap.release()
cv2.destroyAllWindows()
