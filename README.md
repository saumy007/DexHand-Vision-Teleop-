# ROS2 DexHand Vision Teleop

A real-time, AI-powered vision teleoperation pipeline for TheRobotStudio's DexHand V1.0/V2.0 built on ROS 2.

This project bridges raw computer vision tracking with robotic hand kinematics. Using a standard webcam, Google MediaPipe extracts 21 3D hand landmarks, computes finger joint angles through 3D vector geometry, filters tracking noise, and streams smooth `sensor_msgs/JointState` messages into ROS 2 to drive a DexHand digital twin in RViz2.

---

## Features

* **AI Hand Tracking** – Real-time 3D hand landmark extraction using Google MediaPipe.
* **Vector Trigonometry Engine** – Converts 3D landmark coordinates into finger joint angles (Pitch, Flexor, and DIP joints).
* **Anti-Jitter Filtering** – Deadzone thresholding and Exponential Moving Average (EMA) smoothing for stable motion tracking.
* **ROS 2 Native Integration** – Publishes directly to `/joint_states`.
* **Digital Twin Visualization** – Real-time hand motion visualization in RViz2.
* **CPU & GPU Support** – Works with CPU inference via XNNPACK and benefits from GPU acceleration when available.

---

## System Requirements

### Operating System

* Ubuntu 24.04 LTS (ROS 2 Jazzy)
* Ubuntu 22.04 LTS (ROS 2 Humble)

### Hardware

* Webcam
* Minimum 8 GB RAM
* Dedicated GPU (recommended but not required)

---

# Installation Guide

## 1. Install ROS 2

### Configure Locale

```bash
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Configure ROS 2 Repository

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

sudo apt update && sudo apt install curl gnupg2 lsb-release -y

sudo curl -sSL https://raw.githubusercontent.com/ros2/rosdistro/master/ros.key \
-o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu \
$(source /etc/os-release && echo $UBUNTU_CODENAME) main" | \
sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### Install ROS 2 Desktop

For Ubuntu 24.04:

```bash
sudo apt update
sudo apt install ros-jazzy-desktop -y
sudo apt install ros-dev-tools python3-colcon-common-extensions -y
```

For Ubuntu 22.04 replace `jazzy` with `humble`.

### Install Additional Packages

```bash
sudo apt install ros-$ROS_DISTRO-xacro \
ros-$ROS_DISTRO-joint-state-publisher-gui -y
```

### Source ROS 2

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
```

---

## 2. Create the Workspace

```bash
mkdir -p ~/dex_hands_project/src
cd ~/dex_hands_project/src
```

Clone the DexHand description package:

```bash
git clone https://github.com/iotdesignshop/dexhandv2_description.git
```

Build the workspace:

```bash
cd ~/dex_hands_project

colcon build --symlink-install

source install/setup.bash
```

---

## 3. Configure Python Environment

Create a virtual environment:

```bash
cd ~/dex_hands_project

python3 -m venv venv

source venv/bin/activate
```

### Create `requirements.txt`

```txt
opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
```

### Install Dependencies

```bash
pip install --upgrade pip

pip install -r requirements.txt
```

---

## 4. Download the MediaPipe Model

```bash
cd ~/dex_hands_project

curl -O https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

---

## 5. Add the Teleoperation Script

Place your teleoperation script in:

```text
~/dex_hands_project/hand_teleop.py
```

Your workspace should look like:

```text
dex_hands_project/
├── src/
│   └── dexhandv2_description/
├── install/
├── build/
├── log/
├── venv/
├── hand_landmarker.task
├── hand_teleop.py
└── requirements.txt
```

---

# Running the System

Start the components in the order shown below.

---

## Terminal 1 – AI Hand Tracking Node

```bash
cd ~/dex_hands_project

source /opt/ros/$ROS_DISTRO/setup.bash

source venv/bin/activate

python3 hand_teleop.py
```

This process:

* Captures webcam frames
* Detects hand landmarks
* Computes finger joint angles
* Publishes ROS 2 JointState messages

---

## Terminal 2 – RViz2 Visualization

```bash
cd ~/dex_hands_project

source /opt/ros/$ROS_DISTRO/setup.bash

source install/setup.bash

ros2 launch dexhandv2_description display.launch.py
```

This launches:

* Robot State Publisher
* RViz2
* DexHand URDF Model

---

# Important Note

When RViz2 launches, a small window named:

```text
Joint State Publisher
```

may appear.

Close this window immediately.

The Joint State Publisher GUI sends its own joint commands and can conflict with the teleoperation node.

Once closed, the MediaPipe node becomes the sole source of joint commands, enabling smooth real-time teleoperation.

---

# Data Flow

```text
Webcam
   │
   ▼
Google MediaPipe
   │
   ▼
21 Hand Landmarks
   │
   ▼
3D Vector Geometry
   │
   ▼
Joint Angle Computation
   │
   ▼
EMA + Deadzone Filtering
   │
   ▼
ROS2 JointState Messages
   │
   ▼
Robot State Publisher
   │
   ▼
RViz2 Digital Twin
```

---

# Future Improvements

* Bidirectional robot feedback
* Hardware DexHand integration
* ROS2 Control support
* Isaac Sim integration
* VR/XR teleoperation support
* Multi-hand tracking

---

# License

This project is released under the MIT License.

See the LICENSE file for details.
