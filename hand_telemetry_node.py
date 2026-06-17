import cv2
import math
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTeleopNode(Node):
    def __init__(self):
        super().__init__('dexhand_telemetry_node')
        # Create publisher to the topic RViz2 is listening to
        self.publisher_ = self.create_publisher(JointState, '/joint_states', 10)
        
        # NOTE: Updated to match the exact joint names from dexhandv2_description URDF
        self.joint_names = [
            'R_Index_Pitch', 'R_Middle_Pitch', 'R_Ring_Pitch', 'R_Pinky_Pitch',
            'R_Index_Flexor', 'R_Middle_Flexor', 'R_Ring_Flexor', 'R_Pinky_Flexor',
            'R_Index_DIP', 'R_Middle_DIP', 'R_Ring_DIP', 'R_Pinky_DIP',
            'R_Thumb_Yaw', 'R_Thumb_Roll', 'R_Thumb_Flexor', 'R_Thumb_DIP', 'R_Thumb_Pitch',
            'R_Index_Yaw', 'R_Middle_Yaw', 'R_Ring_Yaw', 'R_Pinky_Yaw'
        ]
        
        # Anti-Jitter System
        self.smoothed_angles = {name: 0.0 for name in self.joint_names}
        self.smoothing_factor = 0.1 # Lowered from 0.3: Applies much heavier smoothing
        self.deadzone = 0.02 # Radians (~1.1 degrees): Ignores micro-fluctuations

        self.get_logger().info("DexHand Telemetry Node running. Publishing to /joint_states...")

    def calculate_angle(self, p1, p2, p3):
        """
        Calculate the 3D angle at joint p2, formed by p1-p2-p3.
        Returns the bending angle in radians (0 = straight, PI = fully bent).
        """
        v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
        
        # Cosine rule to find angle
        dot_product = np.dot(v1, v2)
        magnitude_v1 = np.linalg.norm(v1)
        magnitude_v2 = np.linalg.norm(v2)
        
        # Prevent division by zero errors
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
            
        cos_angle = dot_product / (magnitude_v1 * magnitude_v2)
        # Ensure the value is within the valid range for arccos
        cos_angle = max(min(cos_angle, 1.0), -1.0)
        
        # A completely straight finger forms 180 degrees (PI).
        # We want straight to be 0 radians for the robot URDF.
        angle = math.pi - math.acos(cos_angle)
        
        # Scale slightly to match human limits to robot limits (optional mapping)
        return max(0.0, angle * 1.2) 

    def publish_joints(self, landmarks):
        """Calculates angles from landmarks and publishes them to ROS 2."""
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        
        # Calculate raw angles for each finger joint
        raw_angles = {}
        
        # Thumb (Landmarks 0, 1, 2, 3, 4)
        raw_angles['R_Thumb_Yaw'] = 0.0    # Keeping static for stability
        raw_angles['R_Thumb_Pitch'] = 0.0  # Keeping static for stability
        raw_angles['R_Thumb_Roll'] = self.calculate_angle(landmarks[0], landmarks[1], landmarks[2])
        raw_angles['R_Thumb_Flexor'] = self.calculate_angle(landmarks[1], landmarks[2], landmarks[3])
        raw_angles['R_Thumb_DIP'] = self.calculate_angle(landmarks[2], landmarks[3], landmarks[4])

        # Index (Landmarks 0, 5, 6, 7, 8)
        raw_angles['R_Index_Yaw'] = 0.0
        raw_angles['R_Index_Pitch'] = self.calculate_angle(landmarks[0], landmarks[5], landmarks[6])
        raw_angles['R_Index_Flexor'] = self.calculate_angle(landmarks[5], landmarks[6], landmarks[7])
        raw_angles['R_Index_DIP'] = self.calculate_angle(landmarks[6], landmarks[7], landmarks[8])

        # Middle (Landmarks 0, 9, 10, 11, 12)
        raw_angles['R_Middle_Yaw'] = 0.0
        raw_angles['R_Middle_Pitch'] = self.calculate_angle(landmarks[0], landmarks[9], landmarks[10])
        raw_angles['R_Middle_Flexor'] = self.calculate_angle(landmarks[9], landmarks[10], landmarks[11])
        raw_angles['R_Middle_DIP'] = self.calculate_angle(landmarks[10], landmarks[11], landmarks[12])

        # Ring (Landmarks 0, 13, 14, 15, 16)
        raw_angles['R_Ring_Yaw'] = 0.0
        raw_angles['R_Ring_Pitch'] = self.calculate_angle(landmarks[0], landmarks[13], landmarks[14])
        raw_angles['R_Ring_Flexor'] = self.calculate_angle(landmarks[13], landmarks[14], landmarks[15])
        raw_angles['R_Ring_DIP'] = self.calculate_angle(landmarks[14], landmarks[15], landmarks[16])

        # Pinky (Landmarks 0, 17, 18, 19, 20)
        raw_angles['R_Pinky_Yaw'] = 0.0
        raw_angles['R_Pinky_Pitch'] = self.calculate_angle(landmarks[0], landmarks[17], landmarks[18])
        raw_angles['R_Pinky_Flexor'] = self.calculate_angle(landmarks[17], landmarks[18], landmarks[19])
        raw_angles['R_Pinky_DIP'] = self.calculate_angle(landmarks[18], landmarks[19], landmarks[20])

        # Apply smoothing and build the position array
        msg.position = []
        for name in self.joint_names:
            target_angle = raw_angles[name]
            current_angle = self.smoothed_angles[name]
            
            # Deadzone filter: only process the new angle if it moved enough to matter
            if abs(target_angle - current_angle) > self.deadzone:
                # Exponential Moving Average for smooth robotic movements
                self.smoothed_angles[name] = (self.smoothing_factor * target_angle) + \
                                             ((1 - self.smoothing_factor) * current_angle)
            
            msg.position.append(self.smoothed_angles[name])

        # Broadcast the message to the ROS 2 network!
        self.publisher_.publish(msg)

def main():
    # 1. Initialize ROS 2
    rclpy.init()
    node = HandTeleopNode()

    # 2. Initialize MediaPipe
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
    detector = vision.HandLandmarker.create_from_options(options)

    # 3. Open Webcam
    cap = cv2.VideoCapture(0)
    print("Starting ROS2 Camera Node... Press 'q' in the camera window to quit.")

    while cap.isOpened() and rclpy.ok():
        success, frame = cap.read()
        if not success:
            continue

        # Mirror image & convert color
        frame = cv2.flip(frame, 1)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Detect Hand
        detection_result = detector.detect(mp_image)

        if detection_result.hand_landmarks:
            # We only use the first hand found to control the robot arm
            hand_landmarks = detection_result.hand_landmarks[0]
            
            # Calculate angles and publish to ROS 2!
            node.publish_joints(hand_landmarks)

            # Draw visual debug dots
            h, w, _ = frame.shape
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

        # Let ROS 2 handle background tasks briefly
        rclpy.spin_once(node, timeout_sec=0.01)

        cv2.imshow('ROS 2 Hand Telemetry', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()