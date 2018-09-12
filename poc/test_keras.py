from __future__ import print_function
import os 
from tqdm import tqdm
import cv2 as cv
import numpy as np
import argparse
import dlib


import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from keras.models import model_from_yaml




im_w = 150
im_h = 150

# # live_file = "/home/vladimir/Work/face_liveness_detection_data/live1_of/100.png"
# # live_file = "/home/vladimir/Work/face_liveness_detection_data/fake1_of/200.png"
# img = cv2.imread(live_file, cv2.IMREAD_COLOR)

# X = np.array([img], dtype=float)
# X /= 255
# sample = X.reshape((-1, im_h, im_w, 3))

# classes = loaded_model.predict(sample)
# print(classes)

def get_flow(left, right):
  frame1 = cv.imread(left)
  frame2 = cv.imread(right)

  prvs = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
  hsv = np.zeros_like(frame1)
  hsv[...,1] = 255

  next = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
  flow = cv.calcOpticalFlowFarneback(prvs,next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
  mag, ang = cv.cartToPolar(flow[...,0], flow[...,1])
  hsv[...,0] = ang * 180 / np.pi / 2
  hsv[...,2] = cv.normalize(mag, None, 0, 255, cv.NORM_MINMAX)

  return hsv

def process(left, right):
  detector = dlib.get_frontal_face_detector()
  sp = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
  left_img = cv.imread(left)
  left_img = cv.cvtColor(left_img, cv.COLOR_BGR2RGB)
  left_dets = detector(left_img)
  if(len(left_dets) > 0):
    d = left_dets[0]
    shape = sp(left_img, d)
    dlib.save_face_chip(left_img, shape, "left_dlib_chip", size=im_w, padding=0.25)
  else:
    print("left face not found")

  right_img = cv.imread(right)
  right_img = cv.cvtColor(right_img, cv.COLOR_BGR2RGB)
  right_dets = detector(right_img)
  if(len(right_dets) > 0):
    d = right_dets[0]
    shape = sp(right_img, d)
    dlib.save_face_chip(right_img, shape, "right_dlib_chip", size=im_w, padding=0.25)
  else:
    print("right face not found")

  hsv = get_flow("left_dlib_chip.jpg", "right_dlib_chip.jpg")
  img = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
  filename = "optical_flow.png"
  cv.imwrite(filename, img)

  # load YAML and create model
  yaml_file = open('model.yaml', 'r')
  loaded_model_yaml = yaml_file.read()
  yaml_file.close()
  loaded_model = model_from_yaml(loaded_model_yaml)
  # load weights into new model
  loaded_model.load_weights("model.h5")
  print("Loaded model from disk")

  X = np.array([img], dtype=float)
  X /= 255
  sample = X.reshape((-1, im_h, im_w, 3))
  classes = loaded_model.predict(sample)

  if np.argmax(classes) == 1:
    print("live")
  else:
    print("fraud")

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description = 'Process video')
  parser.add_argument('-l', '--leftimage', help="Specify left image")
  parser.add_argument('-r','--rightimage', help="Specify right image")
  # parser.add_argument('-i','--input_of_image', help="Specify right image")
  args = parser.parse_args()
  process(args.leftimage, args.rightimage)