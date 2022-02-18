#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
backend = "glfw"

import glfw
from imgui.integrations.glfw import GlfwRenderer

import OpenGL.GL as gl
from stb import image as im
import imgui
from yolov5 import detect
from file_selector import file_selector
import threading
import glob
import ctypes
from copy import deepcopy
from custom_utils import yolo_to_x0y0, voc_to_yolo

myappid = 'mascit.app.yololab' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

io = None
image_texture, image_width, image_height = None, None, None

frame_data = {

    "num_imgs" : 0,
    "is_running": False,
    "img": "",
    "image_texture" : None,
    "done": True,
    "predictions" : None,
    "imgs" : None,
    "selected_file" : {
        "path": None,
        "idx": 0,
        "texture":None,
        "name": "",
        "image_width" : None,
        "image_height": None
    },
    "labeling": {
        "new_box_requested": False,
        "curr_bbox": None,
        "bboxes" : [{
                    "x_min": 0,
                    "y_min": 0,
                    "x_max": 200,
                    "y_max": 200,
                    "width": 200,
                    "height": 200,
                    "label": "block"
                }],
        "was_mouse_down": False
    },
    "prev_cursor": glfw.ARROW_CURSOR,
    "y_offset": 146,
    "progress": 0,
    "folder_path": "D:/Projects/python/semantics/project/test_final/imgs", #D:/Projects/python/semantics/project/test_final/images
    "model_path": "D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt", #D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt
    "threshold_conf": 0.55,
    "threshold_iou" : 0.45
}



def fb_to_window_factor(window):
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)

    return max(float(fb_w) / win_w, float(fb_h) / win_h)

def main_glfw():
    global image_texture
    global image_width
    global image_height

    def glfw_init():
        width, height = 1024, 900
        window_name = "YoloV5 GUI"
        if not glfw.init():
            print("Could not initialize OpenGL context")
            exit(1)
        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
        glfw.window_hint(glfw.REFRESH_RATE, 60)
        # Create a windowed mode window and its OpenGL context
        window = glfw.create_window(
            int(width), int(height), window_name, None, None
        )

        glfw.make_context_current(window)
        if not window:
            glfw.terminate()
            print("Could not initialize Window")
            exit(1)
        return window
    window = glfw_init()
    impl = GlfwRenderer(window)
    io = impl.io
    frame_data["glfw"] = {"io": io, "window": window}
    x = im.load('chip.png')
    glfw.set_window_icon(window, 1, [(x.shape[1],x.shape[0], x)])
    
    io.fonts.clear()
    font_scaling_factor = fb_to_window_factor(window)
    io.font_global_scale = 1. / font_scaling_factor
    
    io.fonts.add_font_from_file_ttf("Roboto-Regular.ttf", 18, io.fonts.get_glyph_ranges_latin())
    impl.refresh_font_texture()
    
    frame_data["io"] = imgui.get_io()

    prev_img = ""
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        if frame_data["is_running"] and frame_data["img"] != "" and frame_data["img"] != prev_img:
            prev_img = frame_data["img"]
            frame_data["image_texture"], frame_data["image_width"], frame_data["image_height"] = load_image(frame_data["img"])
        
        if frame_data["done"] and frame_data["imgs"] is not None and frame_data["selected_file"]["texture"] is None:
            frame_data["selected_file"]["texture"], frame_data["selected_file"]["image_width"], frame_data["selected_file"]["image_height"] = load_image(frame_data["imgs"][frame_data["selected_file"]["idx"]])

        imgui.new_frame()
        on_frame()
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
        time.sleep(0.0013)

    impl.shutdown()
    glfw.terminate()


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

import shutil
def start_inference(frame_data):
    try:
        shutil.rmtree(frame_data["folder_path"] + "/exp/predictions")
    except:
        pass
    predictions = detect.run(weights=frame_data["model_path"], imgsz=[1280, 1280], conf_thres=frame_data["threshold_conf"], iou_thres=frame_data["threshold_iou"], save_conf=True,
                exist_ok=True, save_txt=True, source=frame_data["folder_path"], project=frame_data["folder_path"] + "/exp", name="predictions",)
        
    for _, (_, img)  in enumerate(predictions):
        # print(img)
        frame_data["img"] = img
        frame_data["progress"] += 0.1
        if not frame_data["is_running"]:
            break
        
    frame_data["is_running"] = False
    frame_data["progress"] = 0
    frame_data["done"] = True
# backend-independent frame rendering function:

def on_frame():
    global frame_data

    labeling = frame_data["labeling"]

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", 'Cmd+Q', False, True
            )
            if clicked_quit:
                exit(1)
            imgui.end_menu()
        imgui.end_main_menu_bar()
    viewport = imgui.get_main_viewport().size
    imgui.set_next_window_size(viewport[0], viewport[1]-25, condition=imgui.ALWAYS)
    imgui.set_next_window_position(0, 25, condition=imgui.ALWAYS)
    flags = ( imgui.WINDOW_NO_MOVE 
        | imgui.WINDOW_NO_TITLE_BAR
        |   imgui.WINDOW_NO_COLLAPSE
        | imgui.WINDOW_NO_RESIZE
        
    )
    
    imgui.begin("Custom window", None, flags=flags)
        
    if frame_data["is_running"]:
        imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha *  0.5)
    imgui.columns(2, "mycolumns3", False)
    # // 3-ways, no border
    
    model_btn_title = "Choose model path..."
    if imgui.button(model_btn_title):
        imgui.open_popup("Choose model path...")

    model_file = file_selector("Choose model path...", False)
    if model_file is not None:
        frame_data["model_path"] = model_file
    
    if frame_data["model_path"] != "":
        imgui.text(frame_data["model_path"])
    
    imgui.next_column()
    
    images_btn_title = "Choose images directory..."
    if imgui.button(images_btn_title):
        imgui.open_popup(images_btn_title)
    images_path = file_selector(images_btn_title, True)
    if images_path is not None:
        frame_data["folder_path"] = images_path
    if frame_data["folder_path"] != "":
        imgui.text(frame_data["folder_path"])
    
    
    imgui.next_column()
    imgui.separator()
    _, frame_data["threshold_conf"] = imgui.slider_float(
                label="Conf. threshold",
                value=frame_data["threshold_conf"],
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            )
    imgui.next_column()
    _, frame_data["threshold_iou"] = imgui.slider_float(
                label="IoU threshold",
                value=frame_data["threshold_iou"],
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            )
    imgui.separator()
    
    if frame_data["is_running"]:
        imgui.internal.pop_item_flag()
        imgui.pop_style_var()

    imgui.columns(1)
    
    #print(imgui.get_mouse_pos())
    
    
    if frame_data["is_running"]:
        start_clicked = imgui.button("Stop analysis")
    else:
        start_clicked = imgui.button("Start analysis")

    if start_clicked:

        if not frame_data["is_running"]:
            frame_data["is_running"] = True
            frame_data["progress"] = 0
            frame_data["done"] = False
            frame_data["predictions"] = {}
            # call model
            imgs = glob.glob(frame_data["folder_path"] + "/*.jpg")
            frame_data["num_imgs"] = len(imgs)
            # print(f"running {frame_data['is_running']}")
            thread = threading.Thread(target=start_inference, args=(frame_data, ))
            thread.start()
        else:
            frame_data["is_running"] = False

    imgui.same_line()
    annotate_click = imgui.button("New box" if not labeling["new_box_requested"] else "Cancel")        

    if annotate_click or imgui.is_key_pressed(glfw.KEY_N):
        labeling["new_box_requested"] = not labeling["new_box_requested"]

    imgui.same_line()
    save_click = imgui.button("Save")

    if save_click:
        if frame_data["predictions"] is not None:
            os.makedirs(frame_data["folder_path"] + "/pseudo/", exist_ok=True)
            for file in frame_data["predictions"]:
                
                with open(frame_data["folder_path"] + f"/exp/predictions/labels/{file.rsplit('.')[0]}.txt", "w") as fp:
                    for bbox in frame_data["predictions"][file]:
                        yolo_coords = voc_to_yolo((frame_data["selected_file"]["image_width"], frame_data["selected_file"]["image_height"]), [bbox["x_min"], bbox["y_min"], bbox["x_max"], bbox["y_max"]])
                        fp.write("0 " + " ".join(["%.6f" % a for a in yolo_coords]) + ' 1\n')
    if frame_data["is_running"]:
        
        imgui.columns(3,"progr", False)
        imgui.next_column()
        imgui.progress_bar(
            fraction=frame_data["progress"] * 10 / frame_data["num_imgs"] , 
            size=(-1, 0.0),
            overlay=f"{int(frame_data['progress'] * 10)}/{frame_data['num_imgs']}"
        )
        imgui.columns(1)
        imgui.spacing()
        if frame_data["image_texture"] is not None:
            imgui.same_line((viewport[0] / 2) - (frame_data["image_width"] / 2))
            imgui.image(frame_data["image_texture"], frame_data["image_width"], frame_data["image_height"])
    
    if frame_data["done"]:
        if frame_data["imgs"] is None:
            frame_data["imgs"] = glob.glob(frame_data["folder_path"] + "/*.jpg") #glob.glob(frame_data["folder_path"] + "/exp/predictions/*.jpg")
            frame_data["predictions"] = {} # glob.glob(frame_data["folder_path"] + "/exp/predictions/labels/*.txt") #glob.glob(frame_data["folder_path"] + "/exp/predictions/*.jpg")
        
        x_offset = (viewport[0] / 5)
        imgui.begin_child(label="files_list", width=x_offset, height=-1, border=False, )
        
        for i, p in enumerate(frame_data["imgs"]):
            clicked, _ = imgui.selectable(
                        label=os.path.basename(p), selected=(frame_data["selected_file"]["idx"] == i)
                    )
            if clicked:
                frame_data["selected_file"]["texture"] = None
                frame_data["selected_file"]["idx"] = i
                frame_data["selected_file"]["name"] = os.path.basename(p)
                if frame_data["predictions"].get(frame_data["selected_file"]["name"]) is None:
                    frame_data["predictions"][frame_data["selected_file"]["name"]] = []
                    with open(frame_data["folder_path"] + f"/exp/predictions/labels/{frame_data['selected_file']['name'].rsplit('.')[0]}.txt", "r") as fp:
                        preds = fp.readlines()
                    for pred in preds:
                        line = pred.strip().split(" ")
                        coords = list(map(lambda x: float(x), line[1:-1]))

                        real_coords = yolo_to_x0y0(coords, frame_data["selected_file"]["image_width"], frame_data["selected_file"]["image_height"], frame_data["selected_file"]["image_width"], frame_data["selected_file"]["image_height"])
                        frame_data["predictions"][frame_data["selected_file"]["name"]]\
                            .append({
                                "x_min": real_coords[0],
                                "y_min": real_coords[1],
                                "x_max": real_coords[2],
                                "y_max": real_coords[3],
                                "width": real_coords[2] - real_coords[0],
                                "height": real_coords[3] - real_coords[1],
                                "label": "block"
                            })

        imgui.end_child()
        imgui.same_line()
        imgui.begin_child(label="img_preview", width=-1, height=-1, border=False,)

        if frame_data["selected_file"]["texture"] is not None:
            imgui.image(frame_data["selected_file"]["texture"], frame_data["selected_file"]["image_width"], frame_data["selected_file"]["image_height"])
        
        draw_list = imgui.get_window_draw_list()
        
        if not imgui.is_mouse_down() and labeling["was_mouse_down"]:
            labeling["was_mouse_down"] = False
            labeling["new_box_requested"] = False
            labeling["curr_bbox"]["width"] = labeling["curr_bbox"]["x_max"] - labeling["curr_bbox"]["x_min"]
            labeling["curr_bbox"]["height"] = labeling["curr_bbox"]["y_max"] - labeling["curr_bbox"]["y_min"]

            frame_data["predictions"][frame_data["selected_file"]["name"]]\
                            .append(deepcopy(labeling["curr_bbox"]))
            if labeling["curr_bbox"] is not None:
                labeling["curr_bbox"] = None
        elif imgui.is_mouse_down() and labeling["new_box_requested"]:

            labeling["was_mouse_down"] = True
            if labeling["curr_bbox"] is None:
                # save coords relative to the image
                labeling["curr_bbox"] = {
                    "x_min": frame_data["io"].mouse_pos[0] - x_offset,
                    "y_min": frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"],
                    "label": "block"
                }
            labeling["curr_bbox"]["x_max"] = frame_data["io"].mouse_pos[0] - x_offset
            labeling["curr_bbox"]["y_max"] = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"]
            # convert image coords to screen coords
            draw_list.add_rect(
                labeling["curr_bbox"]["x_min"] + x_offset, 
                labeling["curr_bbox"]["y_min"] - imgui.get_scroll_y() +  frame_data["y_offset"], 
                labeling["curr_bbox"]["x_max"] + x_offset, 
                labeling["curr_bbox"]["y_max"] - imgui.get_scroll_y() +  frame_data["y_offset"], 
                imgui.get_color_u32_rgba(1,0,0,1), thickness=1)
        else:
            found = []
            if frame_data["predictions"].get(frame_data["selected_file"]["name"]) is not None:

                for bbox in frame_data["predictions"][frame_data["selected_file"]["name"]]:
                    
                    draw_list.add_rect(
                        bbox["x_min"] + x_offset, 
                        bbox["y_min"] - imgui.get_scroll_y() +  frame_data["y_offset"], 
                        bbox["x_max"] + x_offset, 
                        bbox["y_max"] - imgui.get_scroll_y() +  frame_data["y_offset"], 
                        imgui.get_color_u32_rgba(1,0,0,1),
                        thickness=1
                    )

                    if imgui.get_mouse_pos()[0] >= bbox["x_min"] + x_offset  and\
                        imgui.get_mouse_pos()[0] <= bbox["x_max"] + x_offset  and\
                        imgui.get_mouse_pos()[1] >= bbox["y_min"] - imgui.get_scroll_y() +  frame_data["y_offset"]  and\
                        imgui.get_mouse_pos()[1] <=  bbox["y_max"] - imgui.get_scroll_y() +  frame_data["y_offset"] :
                        
                        if frame_data["prev_cursor"] != glfw.HAND_CURSOR:
                            glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.HAND_CURSOR))
                            frame_data["prev_cursor"] = glfw.HAND_CURSOR
                            #print("created")
                        found.append(bbox)
                        
                # take the closest window. Needed for nested bboxes.
                ordered_found = sorted(found, key=lambda x: abs(imgui.get_mouse_pos()[0] - x["x_min"]))

                if len(ordered_found) > 0 and labeling["curr_bbox"] is None:
                    labeling["curr_bbox"] = ordered_found[0]
                if frame_data["prev_cursor"] != glfw.ARROW_CURSOR and found == [] and not imgui.is_mouse_down(1):
                    frame_data["prev_cursor"] = glfw.ARROW_CURSOR
                    glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.ARROW_CURSOR))
                    #print("normal")
            
            if imgui.is_mouse_down() and labeling["curr_bbox"] is not None:

                labeling["curr_bbox"]["x_min"] = frame_data["io"].mouse_pos[0] - x_offset - labeling["curr_bbox"]["width"]/2
                labeling["curr_bbox"]["y_min"] = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"] - labeling["curr_bbox"]["height"]/2
                labeling["curr_bbox"]["x_max"] = labeling["curr_bbox"]["x_min"] + labeling["curr_bbox"]["width"]
                labeling["curr_bbox"]["y_max"] = labeling["curr_bbox"]["y_min"] + labeling["curr_bbox"]["height"]
            
            if imgui.is_mouse_down(1) and labeling["curr_bbox"] is not None:

                labeling["curr_bbox"]["x_max"] = frame_data["io"].mouse_pos[0] - x_offset
                labeling["curr_bbox"]["y_max"] = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"]
                labeling["curr_bbox"]["width"] = abs(labeling["curr_bbox"]["x_max"] - labeling["curr_bbox"]["x_min"])
                labeling["curr_bbox"]["height"] = abs(labeling["curr_bbox"]["y_max"] - labeling["curr_bbox"]["y_min"])
            
            if imgui.is_key_pressed(glfw.KEY_BACKSPACE) and labeling["curr_bbox"] is not None:
                print("backspace")
                frame_data["predictions"].get(frame_data["selected_file"]["name"])\
                    .remove(labeling["curr_bbox"])
                labeling["curr_bbox"] = None

            if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1):
                labeling["curr_bbox"] = None
        imgui.end_child()

    imgui.end()



if __name__ == "__main__":
    imgui.create_context()

    io = imgui.get_io()
    
    backend = "glfw"
    main_glfw()
    