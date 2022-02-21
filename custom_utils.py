from __future__ import annotations
import glfw
import pygame
import OpenGL.GL as gl
from PIL import Image
from math import floor
from copy import deepcopy

from components.data import BBox, ImageInfo

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


def fb_to_window_factor(window):
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)

    return max(float(fb_w) / win_w, float(fb_h) / win_h)

def load_image_from_file(image_name, scale=1):
    image = pygame.image.load(image_name)

    textureSurface = pygame.transform.flip(image, False, True)
    
    orig_width = textureSurface.get_width()
    orig_height = textureSurface.get_height()

    """ print("orig")
    print(orig_width)
    print(orig_height)

    print(f"orig ar: {orig_width/orig_height}") """

    if scale != 1:
        """ w = orig_width * scale
        w = w * (orig_height/orig_width)
        h = orig_height """
        """ basewidth = int(orig_width * scale)
        wpercent = (basewidth/float(orig_width))
        hsize = int((float(orig_height)*float(wpercent))) """
        scaled_w = int(orig_width*scale)
        scaled_h = int(orig_height*scale)
        textureSurface = pygame.transform.smoothscale(textureSurface, [scaled_w, scaled_h] )
    textureData = pygame.image.tostring(textureSurface, "RGB", 1)

    width = textureSurface.get_width()
    height = textureSurface.get_height()

    """ print("scaled")
    print(width)
    print(height)
    print(f"scaled ar: {width/height}") """
    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB,
                    gl.GL_UNSIGNED_BYTE, textureData)

    return {
        "texture": texture, 
        "scaled_width": width, 
        "scaled_height": height, 
        "orig_width": orig_width,
        "orig_height": orig_height
    }

def _load_image_texture(img_id, image_name, imgs_to_render):
    
    img_data = load_image_from_file(image_name, imgs_to_render[img_id]["scale"])
    
    imgs_to_render[img_id]["name"] = image_name
    imgs_to_render[img_id]["texture"] = img_data["texture"]
    imgs_to_render[img_id]["width"] = img_data["orig_width"]
    imgs_to_render[img_id]["height"] = img_data["orig_height"]
    imgs_to_render[img_id]["scaled_width"] = img_data["scaled_width"]
    imgs_to_render[img_id]["scaled_height"] = img_data["scaled_height"]


def load_images(imgs_to_render):

    for key in imgs_to_render:
        img_obj = imgs_to_render[key]
        img_info : ImageInfo = img_obj["img_info"]

        if img_info is not None and (img_obj["texture"] is None or img_obj["prev_name"] != img_obj["name"]\
            or img_obj["prev_scale"] != img_obj["scale"]):
            _load_image_texture(key, img_info.path, imgs_to_render)
            img_obj["prev_name"] = img_obj["name"]
            img_obj["prev_scale"] = img_obj["scale"]


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