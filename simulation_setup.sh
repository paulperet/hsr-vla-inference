# Setup catkin workspace
mkdir /root/catkin_ws
cd /root/catkin_ws
mkdir src
source /opt/ros/noetic/setup.bash && catkin_make
echo "source /root/catkin_ws/devel/setup.bash" >> ~/.bashrc

# Create ROS package
mkdir /root/catkin_ws/src
cd /root/catkin_ws/src
catkin_create_pkg hsr_controller rospy sensor_msgs geometry_msgs trajectory_msgs
cd /root/catkin_ws
source /root/catkin_ws/devel/setup.bash && catkin_make

# Create ROS node script
mkdir /root/catkin_ws/src/hsr_controller/scripts

cp hsr_debug.py /root/catkin_ws/src/hsr_controller/scripts
cp hsr_controller.py /root/catkin_ws/src/hsr_controller/scripts

chmod +x /root/catkin_ws/src/hsr_controller/scripts/hsr_debug.py
chmod +x /root/catkin_ws/src/hsr_controller/scripts/hsr_controller.py

source /root/catkin_ws/devel/setup.bash && catkin_make