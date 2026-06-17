ROS2 DexHand Vision Teleop

A real-time, AI-powered vision teleoperation pipeline for TheRobotStudio's DexHand V1.0/V2.0 built on ROS 2. This repository bridges raw computer vision tracking with high-fidelity robotic kinematics. By using a standard webcam, Google MediaPipe extracts 21 3D hand landmarks, computes individual joint angles via 3D vector geometry, filters out tracking noise, and streams smooth sensor_msgs/JointState arrays directly into a ROS 2 robot state publisher to drive a digital twin in RViz2.

Key Features

AI Gesture Tracking: Real-time 3D landmark extraction using a standard webcam feed via Google MediaPipe.

Vector Trigonometry Engine: Real-time translation of 3D coordinates into relative angular radians for joint state tracking (Pitch, Flexor, and DIP joints).

Anti-Jitter Filtering: Dual-stage signal processing featuring a configurable deadzone threshold and an Exponential Moving Average (EMA) smoothing algorithm to reduce sensor chatter.

ROS 2 Native: Seamless integration with /joint_states and standard robot description packages.

Prerequisites & System Requirements

Operating System: Ubuntu 24.04 LTS (Noble Numbat) or Ubuntu 22.04 LTS (Jammy Jellyfish)

Hardware: Webcam, minimum 8GB RAM, and a dedicated GPU is recommended but not mandatory (CPU fallback via XNNPACK is fully supported).

Step-by-Step Installation & Reproduction Guide

Follow these steps exactly in sequence to set up your environment, install dependencies, and run the teleoperation simulation.

Step 1: Install and Source ROS 2

If you do not have ROS 2 installed on your system, open a terminal and run the following commands sequentially to set up ROS 2 Jazzy (for Ubuntu 24.04) or ROS 2 Humble (for Ubuntu 22.04).

1. Set up your locale, sources, and keys:

sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

sudo apt update && sudo apt install curl gnupg2 lsb-release -y
sudo curl -sSL [https://raw.githubusercontent.com/ros2/rosdistro/master/ros.key](https://raw.githubusercontent.com/ros2/rosdistro/master/ros.key) -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] [http://packages.ros.org/ros2/ubuntu](http://packages.ros.org/ros2/ubuntu) $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null


2. Install ROS 2 Desktop and build tools:

sudo apt update
# Installs ROS 2 Desktop (Change 'jazzy' to 'humble' if you are on Ubuntu 22.04)
sudo apt install ros-jazzy-desktop -y
sudo apt install ros-dev-tools python3-colcon-common-extensions -y


3. Install URDF parsing and xacro packages:

# Change 'jazzy' to 'humble' if running an older distribution
sudo apt install ros-$ROS_DISTRO-xacro ros-$ROS_DISTRO-joint-state-publisher-gui -y


4. Source your main ROS 2 installation:

source /opt/ros/$ROS_DISTRO/setup.bash


Step 2: Set Up the Workspace and Robot Description

We need to set up your target workspace and clone the community robot description meshes for the DexHand.

# Create and move to workspace
mkdir -p ~/dex_hands_project/src
cd ~/dex_hands_project/src

# Clone the description repository
git clone [https://github.com/iotdesignshop/dexhandv2_description.git](https://github.com/iotdesignshop/dexhandv2_description.git)

# Move back to workspace root and build
cd ~/dex_hands_project
colcon build --symlink-install

# Source your local workspace
source install/setup.bash


Step 3: Configure the Python Virtual Environment & Requirements

To prevent system-level package conflicts, we isolate MediaPipe and OpenCV inside a local python virtual environment (venv).

1. Create and activate the virtual environment:

cd ~/dex_hands_project
python3 -m venv venv
source venv/bin/activate


2. Create your requirements.txt file:
Create a file named requirements.txt inside ~/dex_hands_project/ and copy-paste the following text into it:

opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0


3. Install the dependencies:

pip install --upgrade pip
pip install -r requirements.txt


Step 4: Download the MediaPipe Model File

The AI landmarker script relies on a pre-trained task model configuration file to detect human hands. Download it directly into your workspace project folder:

cd ~/dex_hands_project
curl -O [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)


Step 5: Save the Teleop Script

Ensure you have created hand_teleop.py inside ~/dex_hands_project/ and pasted your ROS 2 MediaPipe node code there. It must sit in the same directory alongside the downloaded hand_landmarker.task file and your venv/ folder.

How to Run the Execution Pipeline

Always execute the workflow components in the following strict order using separate terminal shells.

Terminal 1: Run the AI Camera Telemetry Node

This terminal reads your webcam feed, processes hand movements, and pushes the joint telemetry configurations out across the active ROS 2 layer.

# 1. Open a new terminal and navigate to project root
cd ~/dex_hands_project

# 2. Source the main ROS2 system core
source /opt/ros/$ROS_DISTRO/setup.bash

# 3. Activate your Python Virtual Environment
source venv/bin/activate

# 4. Run the node script
python3 hand_teleop.py


Terminal 2: Run the RViz2 Simulation Visualization

This terminal provisions the URDF models and visualizes the hand matrix configurations in real-time.

# 1. Open a second independent terminal window
cd ~/dex_hands_project

# 2. Source the main ROS2 system core
source /opt/ros/$ROS_DISTRO/setup.bash

# 3. Source your compiled workspace configurations
source install/setup.bash

# 4. Launch the display visualizer package
ros2 launch dexhandv2_description display.launch.py


⚠️ Crucial Step for Interaction Stability

When the RViz2 window opens, a secondary tiny GUI window named "Joint State Publisher" containing various manual sliders will automatically appear on your screen.

You must close this small slider window immediately. Click the 'X' to close it. This cuts off conflicting control packets, making your script the sole driver of the virtual hand. Position your hand in front of your camera, and the virtual fingers will mirror your real movements smoothly!
