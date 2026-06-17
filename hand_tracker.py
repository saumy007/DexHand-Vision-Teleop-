import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# 1. Initialize the HandLandmarker
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)

# 2. Open the webcam
cap = cv2.VideoCapture(0)

print("Starting camera... Press 'q' to quit.")

def calculate_hand_orientation(landmarks):
    """
    Calculate hand orientation (roll, pitch, yaw) from landmarks.
    Uses wrist (0), index finger base (5), and pinky base (17) to define palm plane.
    """
    # Get key landmarks
    wrist = np.array([landmarks[0].x, landmarks[0].y, landmarks[0].z])
    index_base = np.array([landmarks[5].x, landmarks[5].y, landmarks[5].z])
    pinky_base = np.array([landmarks[17].x, landmarks[17].y, landmarks[17].z])
    middle_tip = np.array([landmarks[12].x, landmarks[12].y, landmarks[12].z])
    ring_tip = np.array([landmarks[16].x, landmarks[16].y, landmarks[16].z])
    pinky_tip = np.array([landmarks[20].x, landmarks[20].y, landmarks[20].z])
    # Calculate vectors
    
    
    # Calculate direction from wrist to middle finger tip
    
    
    return index_base, pinky_base, middle_tip, ring_tip, pinky_tip

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Mirror the frame horizontally for a natural selfie-view
    frame = cv2.flip(frame, 1)

    # 3. Convert OpenCV BGR format to RGB format for MediaPipe
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    # 4. Detect hands in the frame
    detection_result = detector.detect(mp_image)

    # 5. Extract and Draw ALL 21 3D Coordinates
    if detection_result.hand_landmarks:
        # MediaPipe can detect multiple hands, so we loop through each hand found
        for hand_index, hand_landmarks in enumerate(detection_result.hand_landmarks):
            
            h, w, c = frame.shape
            
            # Loop through all 21 joints/landmarks for the current hand
            for landmark_id, landmark in enumerate(hand_landmarks):
                
                
                # Convert normalized coordinates (0.0 - 1.0) to actual pixel values
                cx, cy = int(landmark.x * w), int(landmark.y * h)

                # Draw a green dot on every single tracked point
                cv2.circle(frame, (cx, cy), 6, (0, 255, 0), cv2.FILLED)
                
                # Optional: Label each dot with its specific ID number (0 to 20)
                # This is highly useful for figuring out which number corresponds to which finger joint
                cv2.putText(frame, str(landmark_id), (cx + 5, cy - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            # Calculate and log hand orientation
            index_base, pinky_base, middle_tip, ring_tip, pinky_tip = calculate_hand_orientation(hand_landmarks)
            print(f"Hand {hand_index} Orientation - Index Base: {index_base}, Pinky Base: {pinky_base}, Middle Tip: {middle_tip}, Ring Tip: {ring_tip}, Pinky Tip: {pinky_tip}")

    # Display the final image
    cv2.imshow('Full Hand Tracking', frame)

    # Break the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up and release the camera
cap.release()
cv2.destroyAllWindows()
