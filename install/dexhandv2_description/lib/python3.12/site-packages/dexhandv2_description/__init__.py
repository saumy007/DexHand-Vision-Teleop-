import os
from ament_index_python.packages import get_package_share_directory

# Inside your DexHandTelemetryNode class __init__ method:
def __init__(self):
    super().__init__('dexhand_telemetry_node')
    
    # 1. Initialize the Publisher
    self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
    
    # 2. Dynamically locate the model file within the package share directory
    package_share_dir = get_package_share_directory('dexhandv2_description')
    model_path = os.path.join(package_share_dir, 'hand_landmarker.task')
    
    # Fallback to local script directory if share directory isn't fully populated yet
    if not os.path.exists(model_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'hand_landmarker.task')
        
    self.get_logger().info(f"Loading MediaPipe model from: {model_path}")
    
    # 3. Initialize MediaPipe with the verified path
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
    self.detector = vision.HandLandmarker.create_from_options(options)
    
    # 4. Initialize Camera & Timer Loop
    self.cap = cv2.VideoCapture(0)
    self.timer = self.create_timer(0.05, self.camera_loop_callback)
    
    self.get_logger().info("DexHand Telemetry Node running. Publishing to /joint_states...")