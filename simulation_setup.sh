# Install python packages
apt-get install -y python3-pip libgl1-mesa-glx
python3 -m pip install opencv-python numpy requests

# Setup catkin workspace
mkdir /home/developer/catkin_ws
cd /home/developer/catkin_ws
mkdir src
source /opt/ros/noetic/setup.bash && catkin_make
echo "source /home/developer/catkin_ws/devel/setup.bash" >> ~/.bashrc

# Create ROS package
mkdir /home/developer/catkin_ws/src
cd /home/developer/catkin_ws/src
catkin_create_pkg hsr_controller rospy sensor_msgs geometry_msgs trajectory_msgs
cd /home/developer/catkin_ws
source /home/developer/catkin_ws/devel/setup.bash && catkin_make

# Create ROS node script
mkdir /home/developer/catkin_ws/src/hsr_controller/scripts

cp /home/developer/hsr-vla-inference/hsr_debug.py /home/developer/catkin_ws/src/hsr_controller/scripts
cp /home/developer/hsr-vla-inference/hsr_controller.py /home/developer/catkin_ws/src/hsr_controller/scripts

chmod +x /home/developer/catkin_ws/src/hsr_controller/scripts/hsr_debug.py
chmod +x /home/developer/catkin_ws/src/hsr_controller/scripts/hsr_controller.py

source /home/developer/catkin_ws/devel/setup.bash && catkin_make