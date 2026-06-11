#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState
from sensor_msgs.msg import CompressedImage

if __name__ == '__main__':
    rospy.init_node('hsr_controller')

    joint_sub = rospy.Subscriber('/hsrb/joint_states', JointState, callback=None)
    image_hand_sub = rospy.Subscriber('/hsrb/head_rgbd_sensor/rgb/image_raw', CompressedImage, callback=None)
    image_head_sub = rospy.Subscriber('/hsrb/hand_camera/image_raw', CompressedImage, callback=None)

    rospy.loginfo("HSR Controller node started.")

    rospy.spin()