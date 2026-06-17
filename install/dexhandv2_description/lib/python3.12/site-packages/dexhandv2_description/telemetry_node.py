import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# --- Vector Math Helpers ---
def get_vector(landmarks, start_idx, end_idx):
    """Helper to get a 3D vector between two MediaPipe landmarks."""
    start = np.array([landmarks[start_idx].x, landmarks[start_idx].y, landmarks[start_idx].z])
    end = np.array([landmarks[end_idx].x, landmarks[end_idx].y, landmarks[end_idx].z])
    return end - start

def calculate_angle(v1, v2):
    """Calculate the angle in radians between two 3D vectors."""
    v1_u = v1 / (np.linalg.norm(v1) + 1e-6)
    v2_u = v2 / (np.linalg.norm(v2) + 1e-6)
    dot_product = np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)
    return np.arccos(dot_product)

class DexHandTelemetryNode(Node):
    def __init__(self):
        super().__init__('dexhand_telemetry_node')
        
        # 1. Initialize the Publisher (/joint_states is the standard ROS 2 topic for robot joints)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # 2. Initialize MediaPipe
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # 3. Initialize Camera
        self.cap = cv2.VideoCapture(0)
        
        # 4. Set Timer Loop (0.05 seconds = 20 Hz)
        self.timer = self.create_timer(0.05, self.camera_loop_callback)
        
        self.get_logger().info("DexHand Telemetry Node running. Publishing to /joint_states...")

    def extract_dexhand_joints(self, landmarks):
        """Maps MediaPipe's 21 landmarks to your 21 specific robotic joint angles."""
        joints = {}
        
        palm_norm = np.cross(get_vector(landmarks, 0, 5), get_vector(landmarks, 0, 17))
        palm_norm = palm_norm / np.linalg.norm(palm_norm)
        mid_axis = get_vector(landmarks, 0, 9)
        
        # --- PITCH ---
        joints['R_Index_Pitch'] = calculate_angle(get_vector(landmarks, 0, 5), get_vector(landmarks, 5, 6))
        joints['R_Middle_Pitch'] = calculate_angle(get_vector(landmarks, 0, 9), get_vector(landmarks, 9, 10))
        joints['R_Ring_Pitch'] = calculate_angle(get_vector(landmarks, 0, 13), get_vector(landmarks, 13, 14))
        joints['R_Pinky_Pitch'] = calculate_angle(get_vector(landmarks, 0, 17), get_vector(landmarks, 17, 18))
        
        # --- FLEXOR ---
        joints['R_Index_Flexor'] = calculate_angle(get_vector(landmarks, 5, 6), get_vector(landmarks, 6, 7))
        joints['R_Middle_Flexor'] = calculate_angle(get_vector(landmarks, 9, 10), get_vector(landmarks, 10, 11))
        joints['R_Ring_Flexor'] = calculate_angle(get_vector(landmarks, 13, 14), get_vector(landmarks, 14, 15))
        joints['R_Pinky_Flexor'] = calculate_angle(get_vector(landmarks, 17, 18), get_vector(landmarks, 18, 19))
        
        # --- DIP ---
        joints['R_Index_DIP'] = calculate_angle(get_vector(landmarks, 6, 7), get_vector(landmarks, 7, 8))
        joints['R_Middle_DIP'] = calculate_angle(get_vector(landmarks, 10, 11), get_vector(landmarks, 11, 12))
        joints['R_Ring_DIP'] = calculate_angle(get_vector(landmarks, 14, 15), get_vector(landmarks, 15, 16))
        joints['R_Pinky_DIP'] = calculate_angle(get_vector(landmarks, 18, 19), get_vector(landmarks, 19, 20))
        
        # --- YAW ---
        joints['R_Index_Yaw'] = calculate_angle(get_vector(landmarks, 0, 5), mid_axis)
        joints['R_Middle_Yaw'] = 0.0 # Reference axis
        joints['R_Ring_Yaw'] = calculate_angle(get_vector(landmarks, 0, 13), mid_axis)
        joints['R_Pinky_Yaw'] = calculate_angle(get_vector(landmarks, 0, 17), mid_axis)
        
        # --- THUMB ---
        joints['R_Thumb_Pitch'] = calculate_angle(get_vector(landmarks, 0, 1), get_vector(landmarks, 1, 2))
        joints['R_Thumb_Yaw'] = calculate_angle(get_vector(landmarks, 0, 1), mid_axis)
        joints['R_Thumb_Roll'] = calculate_angle(get_vector(landmarks, 1, 2), palm_norm)
        joints['R_Thumb_Flexor'] = calculate_angle(get_vector(landmarks, 1, 2), get_vector(landmarks, 2, 3))
        joints['R_Thumb_DIP'] = calculate_angle(get_vector(landmarks, 2, 3), get_vector(landmarks, 3, 4))

        return joints

    def camera_loop_callback(self):
        success, frame = self.cap.read()
        if not success:
            return

        frame = cv2.flip(frame, 1)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        detection_result = self.detector.detect(mp_image)

        if detection_result.hand_landmarks:
            # Grab the first detected hand
            hand_landmarks = detection_result.hand_landmarks[0]
            
            # Get the dictionary of calculated angles in radians
            joint_angles = self.extract_dexhand_joints(hand_landmarks)
            
            # --- CONSTRUCT THE ROS 2 MESSAGE ---
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            
            # JointState messages require two parallel lists: names and positions
            # We extract these directly from our dictionary
            msg.name = list(joint_angles.keys())
            msg.position = list(joint_angles.values())
            
            # Publish to the /joint_states topic
            self.joint_pub.publish(msg)
            
            # Log to terminal (optional, comment out if it's too spammy)
            self.get_logger().info(f"Published 21 joint angles. Index Flexor: {joint_angles['R_Index_Flexor']:.3f} rad")

    def destroy_node(self):
        # Clean up the camera when the node is shut down
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = DexHandTelemetryNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
        
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
