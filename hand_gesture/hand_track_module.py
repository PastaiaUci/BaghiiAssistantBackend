import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, maxHands=1):
        self.maxHands = maxHands
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=self.maxHands)
        self.mpDraw = mp.solutions.drawing_utils

    def getHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def getPos(self, img, handNo=0, draw=True):
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return lmList

    def fingersUp(self):
        fingers = []
        tipIds = [4, 8, 12, 16, 20]
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[0]
            # Thumb
            if myHand.landmark[tipIds[0]].x > myHand.landmark[tipIds[0] - 1].x:
                fingers.append(1)
            else:
                fingers.append(0)
            # 4 Fingers
            for id in range(1, 5):
                if myHand.landmark[tipIds[id]].y < myHand.landmark[tipIds[id] - 2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers

    def isFist(self):
        fingers = self.fingersUp()
        if fingers == [0, 0, 0, 0, 0]:
            return True
        return False
