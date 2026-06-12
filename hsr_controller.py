#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import JointState, CompressedImage
import message_filters
import cv2
import numpy as np

# Store actions
actions = []

# Initialize HSR policy rate
rate = rospy.Rate(30)

def _process_joint_states(msg: JointState):
    return msg.position

def _process_image(msg: CompressedImage):
    rospy.loginfo(f"Received image format: {msg.format}")
    try:
        array = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return image
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

def _process_data(joint_msg: JointState, hand_img_msg: CompressedImage, head_img_msg: CompressedImage):
    joint_positions = _process_joint_states(joint_msg)
    hand_image = _process_image(hand_img_msg)
    head_image = _process_image(head_img_msg)

if __name__ == '__main__':
    rospy.init_node('hsr_controller')
    rospy.loginfo("HSR Controller node started.")

    while not rospy.is_shutdown():
        if len(actions) == 0:
            # Feed a new observation
            joint_sub = rospy.Subscriber('/hsrb/joint_states', JointState)
            image_hand_sub = rospy.Subscriber('/hsrb/hand_camera/image_raw/compressed', CompressedImage)
            image_head_sub = rospy.Subscriber('/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed', CompressedImage)

            time_synchronizer = message_filters.TimeSynchronizer([joint_sub, image_hand_sub, image_head_sub], 10)
            time_synchronizer.registerCallback(_process_data)
        else:
            # Execute the next action
            action = actions.pop(0)
            rate.sleep()