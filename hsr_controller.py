#!/usr/bin/env python3

import rospy
from rospy.numpy_msg import numpy_msg
from rospy import wait_for_message
from sensor_msgs.msg import JointState, CompressedImage, Image
import cv2
from cv_bridge import CvBridge
import numpy as np

import requests
import os

from data_processing import process_data, send_action
from ros_utils import get_sim_and_image_topics
from hsr_topics import base_pub, arm_pub, head_pub, gripper_pub

SERVER_URL = os.environ.get("SERVER_URL", "http://host.docker.internal:8000/predict")
PROMPT = os.environ.get("PROMPT", "Take the cup")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 50))
SYNC_MODE = str(os.environ.get("SYNC_MODE", "sync"))
MAX_TIME = float(os.environ.get("MAX_TIME", 600))

# Total time (excluding inference delay), default 10m
total_time = MAX_TIME

# Store actions
actions = []

# Published topics
published_topics = rospy.get_published_topics()
published_topics = [x for sub in published_topics for x in sub]

# Check if compressed image topics are available
simulation, IMAGE_HAND, IMAGE_HEAD, IMG_TYPE = get_sim_and_image_topics()

if __name__ == '__main__':

    rospy.init_node('hsr_controller')
    rospy.loginfo("HSR Controller node started.")

    print(f"Prompt: {PROMPT}, Max time: {MAX_TIME}s")

    # Initialize HSR policy rate
    rate = rospy.Rate(30) # 30 Hz

    if SYNC_MODE == "sync":
        while not rospy.is_shutdown() and total_time > 0:
            if len(actions) == 0:
                # Feed a new observation
                joint_sub = wait_for_message('/hsrb/joint_states', JointState)

                # Simulation sends multiple messages in the joint_states topic, check for correct type
                if not ('arm_lift_joint' in joint_sub.name):
                    continue

                # Get images observation
                image_hand_sub = wait_for_message(IMAGE_HAND, IMG_TYPE)
                image_head_sub = wait_for_message(IMAGE_HEAD, IMG_TYPE)

                process_data(joint_sub, image_hand_sub, image_head_sub, SERVER_URL, PROMPT, CHUNK_SIZE, simulation) 
            else:
                # Execute the next action
                action = actions.pop(0)

                # Execute current action
                send_action(action, base_pub, arm_pub, head_pub, gripper_pub)
                
                #rospy.loginfo(f"Executing action: {action}")
                rospy.loginfo(f"Remaining time: {total_time}")

                # Subtract the time for one action at 30hz
                total_time -= 1/30

                rate.sleep()