#!/usr/bin/env python3

import rospy
from rospy.numpy_msg import numpy_msg
from rospy import wait_for_message
from sensor_msgs.msg import JointState, CompressedImage, Image
import cv2
from cv_bridge import CvBridge
import numpy as np

import os
import threading

from data_processing import predict_action_chunk, send_action
from ros_utils import get_sim_and_image_topics
from hsr_topics import base_pub, arm_pub, head_pub, gripper_pub

SERVER_URL = os.environ.get("SERVER_URL", "http://host.docker.internal:8000/predict")
PROMPT = os.environ.get("PROMPT", "Take the cup")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 50))
SYNC_MODE = str(os.environ.get("SYNC_MODE", "sync"))
MAX_TIME = float(os.environ.get("MAX_TIME", 600))

# Convert inference time to actions : ASYNC_START_THRESHOLD = t_inference * rate (for 30hz: ASYNC_START_THRESHOLD = t_inference * 30)
# Add a constant delay to compensate for inconsistent communication time : ASYNC_START_THRESHOLD += delay
# Use only if time to produce a new chunk is below or equal to time to consume a new chunk: t_inference < 25 / rate
ASYNC_START_THRESHOLD = float(os.environ.get("ASYNC_START_THRESHOLD", 10))

# Total time (excluding inference delay), default 10m
total_time = MAX_TIME

# Store actions
actions = []

# Published topics
published_topics = rospy.get_published_topics()
published_topics = [x for sub in published_topics for x in sub]

# Check if compressed image topics are available
simulation, IMAGE_HAND, IMAGE_HEAD, IMG_TYPE = get_sim_and_image_topics()

def save_img_hand(img):
    global image_hand_sub
    image_hand_sub = img

def save_img_head(img):
    global image_head_sub
    image_head_sub = img

def save_joint_states(msg):
    global joint_sub
    joint_sub = msg

action_index = 0

actions_lock = threading.Lock()

def produce_actions():

    while True:

        global action_index
        index_at_creation = action_index

        # Simulation sends multiple messages in the joint_states topic, check for correct type
        if not ('arm_lift_joint' in joint_sub.name):
            continue
        
        if action_index == 0 or len(actions) > ASYNC_START_THRESHOLD:
            new_chunk = predict_action_chunk(joint_sub, image_hand_sub, image_head_sub, SERVER_URL, PROMPT, CHUNK_SIZE, simulation)

            with actions_lock:
                global actions
                actions = new_chunk[action_index-index_at_creation:]

            rospy.loginfo(f"Adding {len(actions)} fresh actions")


def consume_actions():
    global total_time
    while not rospy.is_shutdown() and total_time > 0:
        with actions_lock:
            global actions
            if not actions:
                rospy.loginfo("WARNING: Exhausted actions, server may be too slow")
                continue

        consume_single_action()

def consume_single_action():
    global actions
    action = actions.pop(0)

    global action_index, total_time
    action_index += 1

    # Execute current action
    send_action(action, base_pub, arm_pub, head_pub, gripper_pub)
    
    #rospy.loginfo(f"Executing action: {action}")
    rospy.loginfo(f"Remaining time: {total_time}")

    # Subtract the time for one action at 30hz
    total_time -= 1/30

    rate.sleep()

if __name__ == '__main__':
    rospy.init_node('hsr_controller')
    rospy.loginfo("HSR Controller node started.")

    image_hand_sub = wait_for_message(IMAGE_HAND, IMG_TYPE)
    image_head_sub = wait_for_message(IMAGE_HEAD, IMG_TYPE)
    joint_sub = wait_for_message('/hsrb/joint_states', JointState)

    rospy.Subscriber(IMAGE_HAND, IMG_TYPE, save_img_hand, queue_size=1, buff_size=2**24)
    rospy.Subscriber(IMAGE_HEAD, IMG_TYPE, save_img_head, queue_size=1, buff_size=2**24)
    rospy.Subscriber('/hsrb/joint_states', JointState, save_joint_states, queue_size=1)

    rospy.loginfo(f"Mode: {SYNC_MODE}, Prompt: {PROMPT}, Max time: {MAX_TIME}s")

    # Initialize HSR policy rate
    rate = rospy.Rate(30) # 30 Hz

    if SYNC_MODE == "sync":

        while not rospy.is_shutdown() and total_time > 0:
            
            if len(actions) == 0:

                # Simulation sends multiple messages in the joint_states topic, check for correct type
                if not ('arm_lift_joint' in joint_sub.name):
                    continue

                actions = predict_action_chunk(joint_sub, image_hand_sub, image_head_sub, SERVER_URL, PROMPT, CHUNK_SIZE, simulation) 
            else:
                consume_single_action()
    
    elif SYNC_MODE == "async":
        # Create two instances of the Process class, one for each function
        producer = threading.Thread(target=produce_actions)

        # Start both processes
        producer.start()
        consume_actions()

        # Wait for both processes to finish
        producer.join()