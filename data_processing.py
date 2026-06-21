import rospy
from sensor_msgs.msg import JointState, CompressedImage, Image
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import cv2
from cv_bridge import CvBridge  
import requests
import numpy as np 

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def clamp_joint_positions(joint_positions):
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

def process_joint_states(msg: JointState):
    return msg.position

def process_compressed_image(msg: CompressedImage):
    try:
        image = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

def process_raw_image(msg: Image):
    try:
        bridge = CvBridge()
        image = bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        return image
    except cv2.error as error:
        rospy.logerr(f"Error converting image: {error}")

def process_data(joint_msg: JointState, hand_img_msg: CompressedImage, head_img_msg: CompressedImage, server_url: str, prompt: str, chunk_size: int, simulation: bool):
    rospy.loginfo("Processing synchronized data...")
    joint_positions = list(process_joint_states(joint_msg))

    if simulation:
        hand_image = process_raw_image(hand_img_msg).tolist()
        head_image = process_raw_image(head_img_msg).tolist()
        joint_positions = [joint_positions[1]] + [joint_positions[0]] + [joint_positions[2]] + joint_positions[14:] + [joint_positions[7]] + joint_positions[9:11]
    else:
        hand_image = process_compressed_image(hand_img_msg).tolist()
        head_image = process_compressed_image(head_img_msg).tolist()
        joint_positions = [joint_positions[1]] + [joint_positions[0]] + [joint_positions[2]] + joint_positions[11:] + [joint_positions[7]] + joint_positions[9:11]

    resp = requests.post(server_url, json={
        "image_head_tensor": head_image,
        "image_hand_tensor": hand_image,
        "observation": joint_positions,
        "task": prompt
    })

    global actions
    actions = resp.json()["action"][0][:chunk_size]
    rospy.loginfo(f"Done, received {len(actions)} actions.")

def send_action(action, base_pub, arm_pub, head_pub, gripper_pub):

    # Clamp to valid range
    action = clamp_joint_positions(action)

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