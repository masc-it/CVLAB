from __future__ import annotations

from PIL import Image
import os, json
from copy import deepcopy

from cvlab.model.data import BBox, ImageInfo

def yolo_to_x0y0(yolo_pred, input_w, input_h):

    # yolo_x = (x+(w/2))/img_w
    # x_c = (yolo_x) * img_w - (w/2)

    # yolo_width = w/img_w
    # w = yolo_width * img_w

    # target_size / input_size
    """ x_scale = target_w / input_w
    y_scale = target_h / input_h """

    # convert from yolo [x_c, y_c, w_norm, h_norm] to [x0,y0,x1,y1]
    bbox_w = yolo_pred[2] * input_w
    bbox_h = yolo_pred[3] * input_h
    x0_orig = int(yolo_pred[0] * input_w - (bbox_w/2))
    y0_orig = int(yolo_pred[1] * input_h - (bbox_h/2))

    x1_orig = int(yolo_pred[0] * input_w + (bbox_w/2))
    y1_orig = int(yolo_pred[1] * input_h + (bbox_h/2))
    

    """  # scale accoring to target_size
    x = x0_orig * x_scale
    y = y0_orig * y_scale
    xmax = x1_orig * x_scale
    ymax = y1_orig * y_scale """

    x = x0_orig
    y= y0_orig
    xmax= x1_orig
    ymax = y1_orig

    return [x, y, xmax, ymax]

# bbox = (xmin, xmax, ymin, ymax)
# in_size = [w, h]
def resize_bbox(bbox, in_size, out_size):
    bboxx = deepcopy(bbox)
    x_scale = float(out_size[0]) / in_size[0]
    y_scale = float(out_size[1]) / in_size[1]

    # xmin, ymin
    bboxx[0] = x_scale * bboxx[0]
    bboxx[2] = y_scale * bboxx[2]

    # xmax, ymax
    bboxx[1] = x_scale * bboxx[1]
    bboxx[3] = y_scale * bboxx[3]

    return bboxx

def voc_to_yolo(in_size, out_size, box):

    box = resize_bbox(box, in_size, out_size)
    dw = 1./(out_size[0])
    dh = 1./(out_size[1])
    x = (box[0] + box[2])/2.0
    y = (box[1] + box[3])/2.0
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)


def load_img_annotations(img_info : "ImageInfo"):

    img_name = img_info.name
    
    collection = img_info.collection_info

    annotation_file = f"{collection.path}/annotations/{img_name}.json"
    if not os.path.exists(annotation_file):
        return
    with open(annotation_file, "r") as fp:
        data = json.load(fp)

    bboxes = list(map(lambda x: BBox(x["xmin"],x["ymin"],x["xmax"],x["ymax"], x["label"], x["conf"]), data["bboxes"]))

    img_info.add_bboxes(bboxes)
    
def save_img_annotations(img_info : "ImageInfo", scale_imgs=False):
    
    with open(f"{img_info.collection_info.path}/annotations/{img_info.name}.json", "w") as fp:
        scaled_bboxes = []
        if scale_imgs:
            
            for bbox in img_info.bboxes:
                scaled_bboxes.append(bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h)).as_obj())
        else:
            scaled_bboxes = list(map(lambda x: x.as_obj(), img_info.bboxes))

        data = {"collection": img_info.collection_info.id, "bboxes": scaled_bboxes}
        json.dump(data, fp, indent=1 )



def load_yolo_predictions(path, image_width, image_height, scaled_width, scaled_height):

    coords = []
    with open(path, "r") as fp:
        preds = fp.readlines()
    for pred in preds:
        line = pred.strip().split(" ")
        _coords = list(map(lambda x: float(x), line[1:-1]))

        real_coords = yolo_to_x0y0(_coords, scaled_width, scaled_height)

        offset = 0 
        """ if scaled_width > image_width:
            real_coords[0] *= image_width/scaled_width """
            #offset = -1 * scaled_width/image_width * real_coords[0]
        coords.append({
            "x_min": real_coords[0] + offset,
            "y_min": real_coords[1] + offset,
            "x_max": real_coords[2] + offset,
            "y_max": real_coords[3] + offset,
            "width": real_coords[2] - real_coords[0],
            "height": real_coords[3] - real_coords[1],
            "label": line[0],
            "conf": line[-1]
        })
    return coords


def import_yolo_predictions(path, scaled_width, scaled_height):

    bboxes : list[BBox] = []
    with open(path, "r") as fp:
        preds = fp.readlines()
    for pred in preds:
        line = pred.strip().split(" ")
        _coords = list(map(lambda x: float(x), line[1:-1]))

        real_coords = yolo_to_x0y0(_coords, scaled_width, scaled_height)
        bbox = BBox(real_coords[0], real_coords[1], real_coords[2], real_coords[3], line[0], float(line[-1]))
        bboxes.append(bbox)
    return bboxes

def get_image_size(img_path):

    img = Image.open(img_path)
    return [img.size[0], img.size[1]]