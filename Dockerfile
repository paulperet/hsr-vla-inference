FROM ros:noetic-robot


### SETUP SYSTEM ###

# Set bash as default
SHELL ["/bin/bash", "-c"]

# Update system and setup bash
RUN apt-get update && apt-get upgrade -y
RUN echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc

# Install necessary packages for ROS and OpenCV
RUN apt-get install -y python3-pip libgl1-mesa-glx
RUN python3 -m pip install opencv-python numpy requests

### ROS PACKAGE ###

# Setup catkin workspace
WORKDIR /root/catkin_ws
RUN mkdir src
RUN source /opt/ros/noetic/setup.bash && catkin_make
RUN echo "source /root/catkin_ws/devel/setup.bash" >> ~/.bashrc

# Create ROS package
WORKDIR /root/catkin_ws/src
RUN catkin_create_pkg hsr_controller rospy sensor_msgs geometry_msgs trajectory_msgs
WORKDIR /root/catkin_ws
RUN source /root/catkin_ws/devel/setup.bash && catkin_make

# Create ROS node script
RUN mkdir /root/catkin_ws/src/hsr_controller/scripts

COPY hsr_debug.py /root/catkin_ws/src/hsr_controller/scripts
COPY hsr_controller.py /root/catkin_ws/src/hsr_controller/scripts

RUN chmod +x /root/catkin_ws/src/hsr_controller/scripts/hsr_debug.py
RUN chmod +x /root/catkin_ws/src/hsr_controller/scripts/hsr_controller.py

RUN source /root/catkin_ws/devel/setup.bash && catkin_make

# Setup HSR mode
RUN alias hsrb_mode='export ROS_MASTER_URI=http:///192.168.2.138:11311 export PS1="\[\033[41;1;37m\]<hsrb>\[\033[0m\]\w$ "'

### UTILITIES ###

# Install tmux for multiple terminal sessions (optional)
RUN apt-get install -y tmux
# Ping command for network testing (optional)
RUN apt-get install -y iputils-ping
# Discover other devices on the network using nmap (optional)
RUN apt-get install -y nmap