import pyautogui
from hand_gesture.hand_track_module import HandDetector

class GestureControl:
    def __init__(self):
        self.detector = HandDetector(maxHands=1)
        self.last_known_hand_position = None
        self.left_click_performed = False

    def process_frame(self, img):
        img = self.detector.getHands(img)
        lmList = self.detector.getPos(img, draw=True)
        if lmList:
            fingers = self.detector.fingersUp()
            screen_width, screen_height = pyautogui.size()

            # Move the cursor with a fist
            if fingers == [0, 0, 0, 0, 0]:  # Fist
                x, y = lmList[0][1], lmList[0][2]

                if self.last_known_hand_position is None:
                    self.last_known_hand_position = (x, y)
                else:
                    delta_x = x - self.last_known_hand_position[0]
                    delta_y = y - self.last_known_hand_position[1]

                    cursor_x, cursor_y = pyautogui.position()
                    new_x = cursor_x - delta_x
                    new_y = cursor_y + delta_y

                    pyautogui.moveTo(new_x, new_y)

                    self.last_known_hand_position = (x, y)

                self.left_click_performed = False 

            # Perform a left click when only the index finger is raised
            elif fingers == [0, 1, 0, 0, 0]:  # Only index finger raised
                if not self.left_click_performed:
                    pyautogui.click(button='left')
                    self.left_click_performed = True

            # Perform a right click when the index and middle fingers are raised
            elif fingers == [0, 1, 1, 0, 0]:  # Index and middle fingers raised
                pyautogui.click(button='right')
                self.left_click_performed = False

        else:
            self.last_known_hand_position = None

        return img
