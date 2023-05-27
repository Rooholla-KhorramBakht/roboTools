import os
import argparse
import cv2
import rosbag
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from PIL import Image
import pickle
import pandas as pd
import numpy as np
from tqdm import tqdm

import rosbag
from tf2_msgs.msg import TFMessage
from collections import defaultdict

def extract_tf_data(bagfile):
    """
    Extracts transformation (TF) data from a given ROS bag file.
    
    Parameters:
    bagfile (str): The path to the bag file from which to extract TF data.

    Returns:
    dict: A dictionary where the keys are the TF's frame IDs (child frame ID) and the values are lists of tuples. 
    Each tuple represents the time stamp of the frame, pose and the corresponding parent ID of the tf message.

    Example:
    {'tag_id1': [(timestamp2, (x, y, z, rotation), parent_id), ...], 
    'tag_id2': [(timestamp2, (x, y, z, rotation), parent_id), ...], 
    ...}
    """
    bag = rosbag.Bag(bagfile)
    tf_data = defaultdict(list)
    for topic, msg, t in bag.read_messages(topics=['/tf', '/tf_static']):
        for transform in msg.transforms:
            # You can also use child_frame_id depending on your needs
            tag_id = transform.child_frame_id
            parent_id = transform.header.frame_id
            pose = transform.transform
            timestamp = t.to_sec()  # Convert to seconds

            tf_data[tag_id].append((timestamp, parent_id, pose))

    bag.close()
    return tf_data


def bag2Images(bag_file_path, output_dir, image_topic):

    '''
    bag2Images extracts the RGB images published in a ROS bagfile and 
    stores them alongside the corresponding timestamps into a csv file. 

    :param bag_file_path: path to the rosbag file
    :param output_dir:    the output directory where the extracted images and stamps should be stored
    :param image_topic:   the name of the image topic published in the rosbag file. 
    :returns: None
    '''

    image_stamps = [] # Store the image timestamps
    
    bag = rosbag.Bag(bag_file_path, "r")
    bridge = CvBridge()
    count = 0
    for topic, msg, t in tqdm(bag.read_messages(topics=[image_topic])):
        cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        # img_rgb = Image.fromarray(cv_img)
        # img_rgb.save(os.path.join(output_dir, f"{count}.png"))
        img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB )
        cv2.imwrite(os.path.join(output_dir, f"{count}.bmp"), img)
        cv2.imshow('preview', img)
        cv2.waitKey(1)

        image_stamps.append([t.to_nsec(), count])
        count += 1

    image_stamps = np.array(image_stamps)
    df_data = {'timestamp(ns)':image_stamps[:,0],
               'image_idx':image_stamps[:,1]}
    
    bag.close()
    df = pd.DataFrame(data = df_data)
    df.to_csv(os.path.join(output_dir,'stamps.csv'), index=False)
