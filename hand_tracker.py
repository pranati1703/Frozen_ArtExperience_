import mediapipe as mp
import math


class HandTracker:
    def __init__(self, max_hands=2, detection_con=0.7, track_con=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, img, draw=True):
        img_rgb = img[:, :, ::-1] # BGR to RGB
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        
        return img

    def get_positions(self, img, hand_no=0):
        lm_list = []
        if self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, c = img.shape
                for id, lm in enumerate(my_hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
        return lm_list

    def get_fingers_up(self, lm_list):
        if not lm_list:
            return []
            
        fingers_open = []
        
        # Dist helper
        def dist(p1, p2):
            return math.hypot(p1[1] - p2[1], p1[2] - p2[2])
            
        wrist = lm_list[0]
        wrist_pt = (0, wrist[1], wrist[2])

        # 1. Thumb (Tip 4 vs IP 3)
        # Check if tip is further from Pinky MCP (17) than IP is
        # This handles the "outwards" extension
        thumb_tip = (0, lm_list[4][1], lm_list[4][2])
        thumb_ip = (0, lm_list[3][1], lm_list[3][2])
        pinky_mcp = (0, lm_list[17][1], lm_list[17][2])
        
        if dist(thumb_tip, pinky_mcp) > dist(thumb_ip, pinky_mcp):
             fingers_open.append(True)
        else:
             fingers_open.append(False)

        # 2. Other 4 fingers (Tip vs PIP)
        # Index(8), Middle(12), Ring(16), Pinky(20)
        # PIPs: 6, 10, 14, 18
        finger_indices = [(8, 6), (12, 10), (16, 14), (20, 18)]
        
        for tip, pip in finger_indices:
            tip_pt = (0, lm_list[tip][1], lm_list[tip][2])
            pip_pt = (0, lm_list[pip][1], lm_list[pip][2])
            
            # If tip is further from wrist than PIP is, it's open
            if dist(tip_pt, wrist_pt) < dist(pip_pt, wrist_pt):
                fingers_open.append(False)
            else:
                fingers_open.append(True)
                
        return fingers_open

    def is_flat_palm(self, lm_list):
        status = self.get_fingers_up(lm_list)
        if not status: return False
        return all(status)



    def get_handedness(self, hand_no=0):
        if self.results.multi_handedness:
            if hand_no < len(self.results.multi_handedness):
                # MediaPipe returns "Left" for Right hand in selfie view if not flipped?
                # Usually: Label is "Left" or "Right".
                return self.results.multi_handedness[hand_no].classification[0].label
        return None
