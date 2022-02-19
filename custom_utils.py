import glfw
import pygame
import OpenGL.GL as gl

def yolo_to_x0y0(yolo_pred, input_w, input_h, target_w, target_h):

    # yolo_x = (x+(w/2))/img_w
    # x_c = (yolo_x) * img_w - (w/2)

    # yolo_width = w/img_w
    # w = yolo_width * img_w

    # target_size / input_size
    x_scale = target_w / input_w
    y_scale = target_h / input_h

    # convert from yolo [x_c, y_c, w_norm, h_norm] to [x0,y0,x1,y1]
    bbox_w = yolo_pred[2] * input_w
    bbox_h = yolo_pred[3] * input_h
    x0_orig = yolo_pred[0] * input_w - (bbox_w/2)
    y0_orig = yolo_pred[1] * input_h - (bbox_h/2)

    x1_orig = x0_orig + bbox_w
    y1_orig = y0_orig + bbox_h

    # scale accoring to target_size
    x = x0_orig * x_scale
    y = y0_orig * y_scale
    xmax = x1_orig * x_scale
    ymax = y1_orig * y_scale

    return [x, y, xmax, ymax]

def voc_to_yolo(size, box):
    dw = 1./(size[0])
    dh = 1./(size[1])
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

def load_image(image_name):
    image = pygame.image.load(image_name)
    textureSurface = pygame.transform.flip(image, False, True)

    textureData = pygame.image.tostring(textureSurface, "RGB", 1)

    width = textureSurface.get_width()
    height = textureSurface.get_height()

    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB,
                    gl.GL_UNSIGNED_BYTE, textureData)

    return texture, width, height

def load_yolo_predictions(path, image_width, image_height):

    coords = []
    with open(path, "r") as fp:
        preds = fp.readlines()
    for pred in preds:
        line = pred.strip().split(" ")
        _coords = list(map(lambda x: float(x), line[1:-1]))

        real_coords = yolo_to_x0y0(_coords, image_width, image_height, image_width, image_height)
        coords.append({
            "x_min": real_coords[0],
            "y_min": real_coords[1],
            "x_max": real_coords[2],
            "y_max": real_coords[3],
            "width": real_coords[2] - real_coords[0],
            "height": real_coords[3] - real_coords[1],
            "label": "block"
        })
    return coords