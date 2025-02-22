#ifndef YOLOV10_NODE_H
# define YOLOV10_NODE_H

# include <ros/ros.h>
# include <sensor_msgs/Image.h>
# include <sensor_msgs/image_encodings.h>
# include "hum_det/DetModeSwitch.h"
# include "inference.h"
# include "utils.h"
# include <cv_bridge/cv_bridge.h>
# include <chrono>
# include <iostream>
# include <opencv2/highgui.hpp>

const std::string NODE_NAME = "yolov10_node";
const std::string DET_IMG_TOPIC = "/" + NODE_NAME + "/stereo/left/det_image";
// const std::string ORIG_IMG_TOPIC = "/" + NODE_NAME + "/stereo/left/orig_image"; // for experiments
const std::string CAMERA_IMG_TOPIC = "/usb_cam_node/image_raw";
// const std::string CAMERA_IMG_TOPIC = "/improved/usb_cam_node/image_raw";
// const std::string CAMERA_IMG_TOPIC = "/stereo/left/image_raw";
const std::string DET_MODE_SWITCH_SRV = "det_mode_switch";

yolo::Inference* inference;

bool is_on = true;

const short FREQ = 1;
// const short FREQ = 25; // engineer: (0.75 сек)
// const short FREQ = 5; // laptop: работает почему-то медленно (0.18 сек); engineer: наоборот, быстрее (0.715 сек, 0.7 сек)
short camera_img_callback_count = 0;
double time_took_sum = 0.0;
short time_took_count = 0;
// short range_count = 0; // for experiments
// const short RANGE_UPPER_LIMIT = 400; // for experiments

ros::Publisher det_img_publisher;
// ros::Publisher orig_img_publisher; // for experiments
ros::Subscriber camera_img_subscriber;
ros::ServiceServer det_mode_switch_server;

// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer3_ep0-20_yolov10s/best_openvino_conv_model/best.xml";
// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/yolov10s_openvino_conv_model/yolov10s.xml";
const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10s/best_openvino_conv_model/best.xml";
// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer7_ep0-20_yolov10s/best_openvino_conv_model/best.xml";

// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/yolov10n_openvino_conv_model/yolov10n.xml";
// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10n/best_openvino_conv_model/best.xml";

// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/yolov10m_openvino_conv_model/yolov10m.xml";
// const std::string MODEL_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10m/best_openvino_conv_model/best.xml";

// engineer
// const std::string MODEL_PATH = "/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10s/best_openvino_conv_model/best.xml";
// const std::string MODEL_PATH = "/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10n/best_openvino_conv_model/best.xml";
// const std::string MODEL_PATH = "/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer6_ep0-20_yolov10m/best_openvino_conv_model/best.xml";


std::vector<std::string> class_names;

const float CONFIDENCE_THRESHOLD = 0.5;
const float NMS_THRESHOLD = 0.5;

#endif
