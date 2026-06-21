from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import rospy

# linear.x, linear.y, linear.z, angular.x, angular.y, angular.z
base_pub = rospy.Publisher("/hsrb/command_velocity", Twist, queue_size=1)

# arm_lift_joint, arm_flex_joint, arm_roll_joint, wrist_flex_joint, wrist_roll_joint
arm_pub = rospy.Publisher('/hsrb/arm_trajectory_controller/command', JointTrajectory, queue_size=1)

# head_tilt_joint, head_pan_joint
head_pub = rospy.Publisher('/hsrb/head_trajectory_controller/command', JointTrajectory, queue_size=1)

# hand_motor_joint
gripper_pub = rospy.Publisher('/hsrb/gripper_controller/command', JointTrajectory, queue_size=1)