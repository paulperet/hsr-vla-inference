#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState

def _test_callback(msg):
    rospy.loginfo(f"Names: {msg.name}")
    rospy.loginfo(f"Positions: {msg.position}")
    rospy.loginfo(f"Velocities: {msg.velocity}")
    rospy.loginfo(f"Efforts: {msg.effort}")

if __name__ == '__main__':
    rospy.init_node('hsr_controller')

    joint_sub = rospy.Subscriber('/hsrb/joint_states', JointState, callback=_test_callback)
    rospy.loginfo("HSR Controller node started.")

    rospy.spin()