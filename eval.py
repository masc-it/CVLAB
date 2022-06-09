import torch
from PIL import Image
import sys
model = torch.hub.load('ultralytics/yolov5', 'custom', path="best.pt")
im = Image.open(sys.argv[1])  # PIL image

results = model(im, size=1280)  # inference
crops = results.crop(save=True)  # cropped detections dictionary
results.save()