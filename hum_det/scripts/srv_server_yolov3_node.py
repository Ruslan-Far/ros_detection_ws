#!/usr/bin/env python3

import cv2
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import time
from hum_det.srv import *

# Внимание! Теперь файл do_color.py не нужен!-------------------------------------------------------------------------------
# питоновские файлы можно не перекомпилировать

NODE_NAME = "yolov3_node"
is_on = False # по умолчанию алгоритм работать не будет. Как из GUI придет сигнал о начале работы, он начнет работу (True)
# если запускать на Инженере (иначе - закомментить)
# IMG_SUB_TOPIC = "/stereo/left/image_raw"
# если запускать на своем ноутбуке (иначе - закомментить)
IMG_SUB_TOPIC = "/usb_cam_node/image_raw"
TRAIN_HEIGHT = 608
TRAIN_WIDTH = 608
HEIGHT = 480
WIDTH = 744
WINDOW_ORIG = "original"
FREQ = 30
img_callback_count = 0
IMG_PUB_TOPIC = "/detected/stereo/left/image_raw"
DET_MODE_SWITCH_SRV = "det_mode_switch"

CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

# если запускать на Инженере (иначе - закомментить)
# CONFIG_PATH = "/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/cfg/usar_engineer3_yolov3.cfg"
# WEIGHTS_PATH = "/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/very_very_good_weights/usar_engineer3_yolov3_best_2018.weights"
# если запускать на своем ноутбуке (иначе - закомментить)
CONFIG_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/cfg/usar_engineer3_yolov3.cfg"
WEIGHTS_PATH = "/home/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/very_very_good_weights/usar_engineer3_yolov3_best_2018.weights"

FONT_SCALE = 1
THICKNESS = 2
# если запускать на Инженере (иначе - закомментить)
# labels = open("/home/lirs/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/data/usar_engineer3.names").read().strip().split("\n")
# если запускать на своем ноутбуке (иначе - закомментить)
labels = open("/home/ruslan/kpfu/magistracy/ml_models/usar_engineer3_yolov3/data/usar_engineer3.names").read().strip().split("\n")
colors = np.array([[0, 0, 255], [203, 192, 255], [0, 102, 255], [0, 255, 255]], dtype="uint8")

net = cv2.dnn.readNetFromDarknet(CONFIG_PATH, WEIGHTS_PATH)

ln = net.getLayerNames()
ln = [ln[int(i - 1)] for i in net.getUnconnectedOutLayers()]

time_took_sum = 0
time_took_count = 0


def reset_fields():
	global img_callback_count
	global time_took_sum
	global time_took_count

	img_callback_count = 0
	time_took_sum = 0
	time_took_count = 0
	print("reset_fields")


# на основе N итераций посчитать, сколько времени в среднем занимает вывод нейросети за одну итерацию
def print_time_took_mean_sum(time_took):
	global time_took_sum
	global time_took_count

	time_took_sum += time_took
	time_took_count += 1
	if time_took_count == 10: # N == 10
		print("time_took_mean_sum:", time_took_sum / time_took_count)
		time_took_sum = 0
		time_took_count = 0


def run_img_publisher(img_publisher, img_rgb, cv_bridge):
	msg = cv_bridge.cv2_to_imgmsg(img_rgb)
	img_publisher.publish(msg)


# переключаем режим "human_detection"
def handle_det_mode_switch(req):
	global is_on

	is_on = req.is_on
	if is_on:
		reset_fields()
	return ModeSwitchResponse(0)


def img_callback(msg: Image, cv_bridge: CvBridge, img_publisher: rospy.Publisher) -> None:
	global is_on
	global img_callback_count

	if not is_on:
		return
	# иначе будет серое байеризованное
	img_bgr = cv_bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
	# иначе будет bgr (если запускать на Инженере (иначе - закомментить)). И намного хуже будет распознавать нейронка
	# img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
	# если запускать на своем ноутбуке (иначе - закомментить)
	img_rgb = img_bgr
	# ОБЯЗАТЕЛЬНО НАДО ДЕЛАТЬ ВМЕСТЕ С cv2.dnn.blobFromImage
	img_rgb = cv2.resize(img_rgb, (TRAIN_WIDTH, TRAIN_HEIGHT))

	if img_callback_count == 0:
		blob = cv2.dnn.blobFromImage(img_rgb, 1/255.0, (TRAIN_WIDTH, TRAIN_HEIGHT), swapRB=False, crop=False) # edited swapRB
		net.setInput(blob)
		start = time.perf_counter()
		layer_outputs = net.forward(ln)
		time_took = time.perf_counter() - start
		print("time_took:", time_took)
		print_time_took_mean_sum(time_took)
		boxes, confidences, class_ids = [], [], []

		# loop over each of the layer outputs
		for output in layer_outputs:
			# loop over each of the object detections
			for detection in output:
				# extract the class id (label) and confidence (as a probability) of
				# the current object detection
				scores = detection[5:]
				class_id = np.argmax(scores)
				confidence = scores[class_id]
				# discard weak predictions by ensuring the detected
				# probability is greater than the minimum probability
				if confidence > CONFIDENCE_THRESHOLD:
					# scale the bounding box coordinates back relative to the
					# size of the image, keeping in mind that YOLO actually
					# returns the center (x, y)-coordinates of the bounding
					# box followed by the boxes' width and height

					box = detection[:4] * np.array([TRAIN_WIDTH, TRAIN_HEIGHT, TRAIN_WIDTH, TRAIN_HEIGHT])
					(centerX, centerY, width, height) = box.astype("int")

					# use the center (x, y)-coordinates to derive the top and
					# and left corner of the bounding box
					x = int(centerX - (width / 2))
					y = int(centerY - (height / 2))

					# update our list of bounding box coordinates, confidences,
					# and class IDs
					boxes.append([x, y, int(width), int(height)])
					confidences.append(float(confidence))
					class_ids.append(class_id)

		# perform the non maximum suppression given the scores defined before
		idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, IOU_THRESHOLD)

		# ensure at least one detection exists
		if len(idxs) > 0:
			# loop over the indexes we are keeping
			for i in idxs.flatten():
				# extract the bounding box coordinates
				x, y = boxes[i][0], boxes[i][1]
				w, h = boxes[i][2], boxes[i][3]
				# draw a bounding box rectangle and label on the image
				color = [int(c) for c in colors[class_ids[i]]]
				cv2.rectangle(img_rgb, (x, y), (x + w, y + h), color=color, thickness=THICKNESS)
				text = f"{labels[class_ids[i]]}: {confidences[i]:.2f}"
				# calculate text width & height to draw the transparent boxes as background of the text
				(text_width, text_height) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=FONT_SCALE, thickness=THICKNESS)[0]
				text_offset_x = x
				text_offset_y = y - 5
				box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width + 2, text_offset_y - text_height))
				overlay = img_rgb.copy()
				cv2.rectangle(overlay, box_coords[0], box_coords[1], color=color, thickness=cv2.FILLED)
				# add opacity (transparency to the box)
				img_rgb = cv2.addWeighted(overlay, 0.6, img_rgb, 0.4, 0)
				# now put the text (label: confidence %)
				cv2.putText(img_rgb, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
					fontScale=FONT_SCALE, color=(0, 0, 0), thickness=THICKNESS)
		img_rgb = cv2.resize(img_rgb, (WIDTH, HEIGHT))
		# отправить для показа в GUI
		run_img_publisher(img_publisher, img_rgb, cv_bridge)
		# просто для показа
		cv2.imshow(NODE_NAME, img_rgb)
		cv2.waitKey(1)
	img_callback_count += 1
	if img_callback_count == FREQ:
		img_callback_count = 0
	# cv2.imshow(WINDOW_ORIG, img_rgb) # вдруг пригодится в процессе экспериментов
	# cv2.waitKey(1)


def main() -> None:
	rospy.init_node(NODE_NAME)
	sample: Image = rospy.wait_for_message(IMG_SUB_TOPIC, Image, timeout=3.0)
	if sample is not None:
		rospy.loginfo(f"Encoding: {sample.encoding}, Resolution: {sample.width, sample.height}")
	cv_bridge: CvBridge = CvBridge()

	img_publisher = rospy.Publisher(IMG_PUB_TOPIC, Image, queue_size=1)
	rospy.Subscriber(IMG_SUB_TOPIC, Image, lambda msg: img_callback(msg, cv_bridge, img_publisher), queue_size=None)
	rospy.Service(DET_MODE_SWITCH_SRV, ModeSwitch, handle_det_mode_switch)

	rospy.spin()

	cv2.destroyAllWindows()


if __name__ == '__main__':
	main()
