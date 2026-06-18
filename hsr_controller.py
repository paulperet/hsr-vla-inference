#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import JointState, CompressedImage, Image
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from rospy import wait_for_message
import cv2
from cv_bridge import CvBridge
import numpy as np

import requests
import os

SERVER_URL = os.environ.get("SERVER_URL", "http://host.docker.internal:8000/predict")
PROMPT = os.environ.get("PROMPT", "Take the cup")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 50))

# Total time (excluding inference delay), default 10m
MAX_TIME = float(os.environ.get("MAX_TIME", 600))
total_time = MAX_TIME

# Store actions
actions = []

# Published topics
published_topics = rospy.get_published_topics()
published_topics = [x for sub in published_topics for x in sub]

# Check if compressed image topics are available
simulation = False
if '/hsrb/hand_camera/image_raw/compressed' not in published_topics and '/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed' not in published_topics:
    simulation = True
    bridge = CvBridge()
    rospy.logwarn("Simulation environment detected.")

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def _clamp_joint_positions(joint_positions):
    joints_limits = {
        'arm_lift_joint': (0.0, 0.69),
        'arm_flex_joint': (-2.62, 0.0),
        'arm_roll_joint': (-2.09, 3.84),
        'wrist_flex_joint': (-1.92, 1.22),
        'wrist_roll_joint': (-1.92, 3.67),
        'head_tilt_joint': (-1.57, 0.52),
        'head_pan_joint': (-3.84, 1.75),
        'hand_motor_joint': (-0.798, 1.24)
    }

    joints = ['arm_lift_joint', 'arm_flex_joint', 'arm_roll_joint', 'wrist_flex_joint', 'wrist_roll_joint', 'hand_motor_joint', 'head_pan_joint', 'head_tilt_joint']

    for i, joint in enumerate(joints):
        joint_positions[i] = clamp(joint_positions[i], joints_limits[joint][0], joints_limits[joint][1])

    return joint_positions

def _process_joint_states(msg: JointState):
    return msg.position

def _process_compressed_image(msg: CompressedImage):
    try:
        image = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if msg.encoding == 'bgr8':
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

def _process_raw_image(msg: Image):
    try:
        image = bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        return image
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

def _process_data(joint_msg: JointState, hand_img_msg: CompressedImage, head_img_msg: CompressedImage):
    rospy.loginfo("Processing synchronized data...")
    joint_positions = list(_process_joint_states(joint_msg))

    if simulation:
        hand_image = _process_raw_image(hand_img_msg).tolist()
        head_image = _process_raw_image(head_img_msg).tolist()
        joint_positions = [joint_positions[1]] + [joint_positions[0]] + [joint_positions[2]] + joint_positions[14:] + [joint_positions[7]] + joint_positions[9:11]
    else:
        hand_image = _process_compressed_image(hand_img_msg).tolist()
        head_image = _process_compressed_image(head_img_msg).tolist()
        joint_positions = [joint_positions[1]] + [joint_positions[0]] + [joint_positions[2]] + joint_positions[11:] + [joint_positions[7]] + joint_positions[9:11]

    resp = requests.post(SERVER_URL, json={
        "image_head_tensor": head_image,
        "image_hand_tensor": hand_image,
        "observation": joint_positions,
        "task": PROMPT
    })

    global actions
    actions = resp.json()["action"][0][:CHUNK_SIZE]
    rospy.loginfo(f"Done, received {len(actions)} actions.")

if __name__ == '__main__':

    rospy.init_node('hsr_controller')
    rospy.loginfo("HSR Controller node started.")

    print(f"Prompt: {PROMPT}, Max time: {MAX_TIME}s")

    # Initialize HSR policy rate
    rate = rospy.Rate(30) # 30 Hz

    # linear.x, linear.y, linear.z, angular.x, angular.y, angular.z
    base_pub = rospy.Publisher("/hsrb/command_velocity", Twist, queue_size=1)

    # arm_lift_joint, arm_flex_joint,arm_roll_joint, wrist_flex_joint, wrist_roll_joint
    arm_pub = rospy.Publisher('/hsrb/arm_trajectory_controller/command', JointTrajectory, queue_size=1)

    # head_tilt_joint, head_pan_joint
    head_pub = rospy.Publisher('/hsrb/head_trajectory_controller/command', JointTrajectory, queue_size=1)

    # hand_motor_joint
    gripper_pub = rospy.Publisher('/hsrb/gripper_controller/command', JointTrajectory, queue_size=1)

    while not rospy.is_shutdown() and total_time > 0:
        if len(actions) == 0:
            # Feed a new observation
            joint_sub = wait_for_message('/hsrb/joint_states', JointState)

            # Simulation sends multiple messages in the joint_states topic, check for correct type
            if not ('arm_lift_joint' in joint_sub.name):
                continue

            if simulation:
                image_hand_sub = wait_for_message('/hsrb/hand_camera/image_raw', Image)
                image_head_sub = wait_for_message('/hsrb/head_rgbd_sensor/rgb/image_rect_color', Image)
            else:
                image_hand_sub = wait_for_message('/hsrb/hand_camera/image_raw/compressed', CompressedImage)
                image_head_sub = wait_for_message('/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed', CompressedImage)

            _process_data(joint_sub, image_hand_sub, image_head_sub) 
        else:
            # Execute the next action
            action = actions.pop(0)

            # Clamp to valid range
            action = _clamp_joint_positions(action)
            
            #rospy.loginfo(f"Executing action: {action}")
            rospy.loginfo(f"Remaining time: {total_time}")

            base_cmd = Twist()
            base_cmd.linear.x = action[8]
            base_cmd.linear.y = action[9]
            base_cmd.angular.z = action[10]

            arm_cmd = JointTrajectory()
            arm_cmd.joint_names = ['arm_lift_joint', 'arm_flex_joint', 'arm_roll_joint', 'wrist_flex_joint', 'wrist_roll_joint']
            p = JointTrajectoryPoint()
            p.positions = action[:5]
            p.time_from_start = rospy.Duration(1)
            arm_cmd.points = [p]

            head_cmd = JointTrajectory()
            head_cmd.joint_names = ['head_tilt_joint', 'head_pan_joint']
            p = JointTrajectoryPoint()
            p.positions = [action[7]] + [action[6]]
            p.time_from_start = rospy.Duration(1)
            head_cmd.points = [p]

            gripper_cmd = JointTrajectory()
            gripper_cmd.joint_names = ['hand_motor_joint']
            p = JointTrajectoryPoint()
            p.positions = [action[5]]
            p.time_from_start = rospy.Duration(1)
            gripper_cmd.points = [p]

            base_pub.publish(base_cmd)
            arm_pub.publish(arm_cmd)
            head_pub.publish(head_cmd)
            gripper_pub.publish(gripper_cmd)

            # Subtract the time for one action at 30hz
            total_time -= 1/30

            rate.sleep()