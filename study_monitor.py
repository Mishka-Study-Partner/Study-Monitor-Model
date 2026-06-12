import cv2
import mediapipe as mp

mp_face = mp.solutions.face_detection
mp_pose = mp.solutions.pose

class StudyMonitor:
    def __init__(self):
        self.face_detection = mp_face.FaceDetection(model_selection=0)
        self.pose = mp_pose.Pose(
            model_complexity=0, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Calibration variables
        self.calibrated = False
        self.calibration_frames = 0
        self.baseline_neck_distance = 0.0
        self.baseline_shoulder_y = 0.0
        self.baseline_face_height = 0.0

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 1. Run Face Detection
        face_results = self.face_detection.process(rgb_frame)
        
        # 2. Run Pose Detection
        pose_results = self.pose.process(rgb_frame)

        status = "FOCUSING"
        color = (0, 255, 0) # Green

        # CHECK 1: Is the user there?
        if not face_results.detections:
            return frame, "NO USER DETECTED", (0, 0, 255)

        # Get Face Geometry
        detection = face_results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        face_height = bbox.height
        face_center_y = bbox.ymin + (face_height / 2)

        # CHECK 2: Posture Logic with Auto-Calibration
        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            left_shoulder_y = landmarks[11].y
            right_shoulder_y = landmarks[12].y
            avg_shoulder_y = (left_shoulder_y + right_shoulder_y) / 2
            
            # The vertical gap between face and shoulders
            current_neck_distance = avg_shoulder_y - face_center_y

            # --- CALIBRATION STEP ---
            if not self.calibrated:
                self.calibration_frames += 1
                self.baseline_neck_distance += current_neck_distance
                self.baseline_shoulder_y += avg_shoulder_y
                self.baseline_face_height += face_height
                
                if self.calibration_frames >= 30:
                    self.baseline_neck_distance /= 30
                    self.baseline_shoulder_y /= 30
                    self.baseline_face_height /= 30
                    self.calibrated = True
                    print(f"✅ Posture Calibrated! Baseline neck: {self.baseline_neck_distance:.3f}")
                
                return frame, "CALIBRATING POSTURE...", (255, 255, 0)

            # --- LEANING FORWARD CUSHION ---
            is_leaning_forward = face_height > (self.baseline_face_height * 1.05)
            dynamic_tolerance = 0.70 if is_leaning_forward else 0.80

            # --- TESTING AGAINST YOUR INDIVIDUAL BASELINE ---
            if current_neck_distance < (self.baseline_neck_distance * dynamic_tolerance):
                status = "BAD POSTURE"
                color = (0, 165, 255) # Orange
            elif avg_shoulder_y > (self.baseline_shoulder_y + 0.14):
                status = "BAD POSTURE"
                color = (0, 165, 255) # Orange

        # CHECK 3: Face Gaze
        if status == "FOCUSING":
            nose = detection.location_data.relative_keypoints[2]
            center_x = bbox.xmin + (bbox.width / 2)
            offset = abs(nose.x - center_x) / bbox.width
            
            if offset > 0.24: 
                status = "LOOKING AWAY"
                color = (0, 165, 255)

        return frame, status, color

    def close(self):
        """
        Explicitly release unmanaged memory graphs allocated by 
        the MediaPipe C++ bindings when a session closes.
        """
        try:
            self.face_detection.close()
            self.pose.close()
            print("🧹 MediaPipe system resource segments cleanly disposed.")
        except Exception:
            pass