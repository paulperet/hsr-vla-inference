#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState, CompressedImage
import cv2
import numpy as np

def _process_joint_states(msg: JointState):
    rospy.loginfo(f"Received joint states: {msg.position}")

def _process_image(msg: CompressedImage):
    rospy.loginfo(f"Received image format: {msg.format}")
    try:
        array = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        rospy.loginfo(f"Converted image shape: {image.shape}")
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

if __name__ == '__main__':
    rospy.init_node('hsr_controller')

    joint_sub = rospy.Subscriber('/hsrb/joint_states', JointState, callback=None)
    image_hand_sub = rospy.Subscriber('/hsrb/hand_camera/image_raw/compressed', CompressedImage, callback=_process_image)
    image_head_sub = rospy.Subscriber('/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed', CompressedImage, callback=_process_image)

    rospy.loginfo("HSR Controller node started.")

    rospy.spin()