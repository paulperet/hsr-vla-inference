import rospy
from sensor_msgs.msg import CompressedImage, Image

def get_sim_and_image_topics():

    # Published topics
    published_topics = rospy.get_published_topics()
    published_topics = [x for sub in published_topics for x in sub]

    # Check if compressed image topics are available
    simulation = False
    IMAGE_HAND = '/hsrb/hand_camera/image_raw/compressed'
    IMAGE_HEAD = '/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed'
    IMG_TYPE = CompressedImage

    if '/hsrb/hand_camera/image_raw/compressed' not in published_topics and '/hsrb/head_rgbd_sensor/rgb/image_rect_color/compressed' not in published_topics:
        simulation = True
        IMAGE_HAND = '/hsrb/hand_camera/image_raw'
        IMAGE_HEAD = '/hsrb/head_rgbd_sensor/rgb/image_rect_color'
        rospy.logwarn("Simulation environment detected.")
        IMG_TYPE = Image

    return simulation, IMAGE_HAND, IMAGE_HEAD, IMG_TYPE