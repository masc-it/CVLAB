import imgui
from components.data import BBox, ImageInfo, Labels
from variables import frame_data
import threading
from yolov5 import detect
from .file_selector import file_selector
import glob, os
import custom_utils
import glfw
from copy import deepcopy
from .projects import Project

def start_inference(frame_data):
    
    predictions = detect.run(weights=frame_data["model_path"], imgsz=[1280, 1280], conf_thres=frame_data["threshold_conf"], iou_thres=frame_data["threshold_iou"], save_conf=True,
                exist_ok=True, save_txt=True, source=frame_data["folder_path"], project=frame_data["folder_path"] + "/exp", name="predictions",)
    
    frame_data["imgs_to_render"]["inference_preview"]["scale"] = 1
    for _, (_, img)  in enumerate(predictions):
        # print(img)
        frame_data["imgs_to_render"]["inference_preview"]["name"] = img
        # frame_data["img"] = img
        frame_data["progress"] += 0.1
        if not frame_data["is_running"]:
            break
        
    frame_data["is_running"] = False
    frame_data["progress"] = 0
    frame_data["done"] = True

def header():
    global frame_data
    
    if imgui.begin_tab_bar("sections"):

        if imgui.begin_tab_item("LAB")[0]:

            header_lab()
            preview()
            imgui.end_tab_item()
        
        if imgui.begin_tab_item("Auto annotation")[0]:
            header_auto_annotation()
            inference_progress()
            if frame_data["done"]:
                preview()
            imgui.end_tab_item()
        
        if imgui.begin_tab_item("Settings")[0]:
            imgui.end_tab_item()
        imgui.end_tab_bar()


def header_lab():
    global frame_data
    labeling = frame_data["labeling"]

    project : Project = frame_data["project"]
    annotate_click = imgui.button("New box" if not labeling["new_box_requested"] else "Cancel")        

    if annotate_click or imgui.is_key_pressed(glfw.KEY_N):
        labeling["new_box_requested"] = not labeling["new_box_requested"]

    imgui.same_line()
    save_click = imgui.button("Save")

    if save_click:

        project.save_annotations()
        """ if frame_data["predictions"] is not None:
            for file in frame_data["predictions"]:
                
                with open(frame_data["folder_path"] + f"/exp/predictions/labels/{file.rsplit('.')[0]}.txt", "w") as fp:
                    for bbox in frame_data["predictions"][file]:
                        yolo_coords = custom_utils.voc_to_yolo(
                            (frame_data["imgs_info"][file]["scaled_size"][0], frame_data["imgs_info"][file]["scaled_size"][1]),
                            (frame_data["imgs_info"][file]["orig_size"][0], frame_data["imgs_info"][file]["orig_size"][1]), 
                            [float(bbox["x_min"]), float(bbox["y_min"]), float(bbox["x_max"]), float(bbox["y_max"])])
                        fp.write(f'{bbox["label"]} ' + " ".join([str(a) for a in yolo_coords]) + f' {bbox["conf"]}\n')
 """
    imgui.same_line()
    labels_click = imgui.button("Labels")

    if labels_click:
        imgui.open_popup("Labels")
    _open_labels_popup(project.labels)

    imgui.same_line()
    scale_changed, frame_data["img_scale"] = imgui.slider_float(
                label="Zoom",
                value=frame_data["img_scale"],
                min_value=0.5,
                max_value=2.0,
                format="%.1f",
            )
    if scale_changed:
        frame_data["scale_changed"] = True


def header_auto_annotation():
    global frame_data

    project : Project = frame_data["project"]
    if frame_data["is_running"]:
        imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha *  0.5)
    imgui.columns(2, "header_2", False)

    model_btn_title = "Choose model path..."
    if imgui.button(model_btn_title):
        imgui.open_popup("Choose model path...")

    model_file = file_selector("Choose model path...", False)
    if model_file is not None:
        project.model_path = model_file
    
    if project.model_path != "":
        imgui.text(project.model_path)
    
    imgui.next_column()
    
    """ images_btn_title = "Choose images directory..."
    if imgui.button(images_btn_title):
        imgui.open_popup(images_btn_title)
    images_path = file_selector(images_btn_title, True)
    if images_path is not None:
        project.pa = images_path
    if frame_data["folder_path"] != "":
        imgui.text(frame_data["folder_path"]) """
    
    
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

            imgs = glob.glob(frame_data["folder_path"] + "/*.jpg")
            frame_data["num_imgs"] = len(imgs)

            thread = threading.Thread(target=start_inference, args=(frame_data, ))
            thread.start()
        else:
            frame_data["is_running"] = False

    imgui.same_line()
    scale_changed, frame_data["img_scale"] = imgui.slider_float(
                label="Zoom",
                value=frame_data["img_scale"],
                min_value=0.5,
                max_value=2.0,
                format="%.1f",
            )
    if scale_changed:
        frame_data["scale_changed"] = True

def _open_labels_popup(labels : Labels):
    
    imgui.set_next_window_size(700, 350)
    if imgui.begin_popup_modal("Labels", flags=imgui.WINDOW_NO_RESIZE )[0]:
        
        imgui.begin_child(label="labels_table", height=250, border=False, )
        imgui.begin_table("labels_t", 4, inner_width=700, flags=imgui.TABLE_SIZING_FIXED_FIT|imgui.TABLE_RESIZABLE)

        imgui.table_setup_column("INDEX",init_width_or_weight=100, )
        imgui.table_setup_column("LABEL",init_width_or_weight=350)
        imgui.table_setup_column("COLOR",init_width_or_weight=50)
        imgui.table_setup_column("SHORTCUT",init_width_or_weight=100)

        imgui.table_headers_row()
        
        for label_obj in labels:
            imgui.table_next_row()
            imgui.table_set_column_index(0)
            imgui.text(str(label_obj.index))
            imgui.table_set_column_index(1)
            imgui.push_item_width(-1)
            _,label_obj.label= imgui.input_text(label=f"lab_{label_obj.index}", value=label_obj.label, buffer_length=128)
            imgui.pop_item_width()
            imgui.table_set_column_index(2)
            
            _, label_obj.rgb = imgui.color_edit3(
                    f"edit_{label_obj.index}", *label_obj.rgb, flags=
                        imgui.COLOR_EDIT_NO_LABEL|imgui.COLOR_EDIT_NO_INPUTS|imgui.COLOR_EDIT_INPUT_RGB
                )
            imgui.table_set_column_index(3)
            imgui.push_item_width(-1)
            short_changed, shortcut= imgui.input_text(label=f"shortcut_{label_obj.index}", value=label_obj.shortcut, buffer_length=2)
            if short_changed:
                try:
                    int(shortcut)
                    if labels.shortcuts.get(shortcut) is None:
                        del labels.shortcuts[label_obj.shortcut] # del old shortcut
                        label_obj.shortcut = shortcut
                        labels.shortcuts[shortcut] = label_obj
                except:
                    pass
                
            imgui.pop_item_width()
             
        imgui.end_table()
        imgui.end_child()

        if imgui.button("Close"):
            imgui.close_current_popup()
        imgui.end_popup()

def inference_progress():
    global frame_data
    img_data = frame_data["imgs_to_render"]["inference_preview"]
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
        if img_data["texture"] is not None:
            imgui.same_line((frame_data["viewport"][0] / 2) - (img_data["width"] / 2))
            imgui.image(img_data["texture"], img_data["width"], img_data["height"])

def preview():
    _files_list()
    _annotation_screen()


def _files_list():
    global frame_data
    project : Project = frame_data["project"]
    img_data = frame_data["imgs_to_render"]["annotate_preview"]
    
    frame_data["x_offset"] = int(frame_data["viewport"][0] / 5)
    #print(frame_data["x_offset"])
    imgui.begin_child(label="files_list", width=frame_data["x_offset"], height=-1, border=False, )
    
    for i, k in enumerate(project.imgs):

        img_info = project.imgs[k]
        name = img_info.name
        clicked, _ = imgui.selectable(
                    label=name, selected=(frame_data["selected_file"]["idx"] == i)
                )
        if clicked or frame_data["scale_changed"]:
            
            img_data["scale"] = frame_data["img_scale"]
            if clicked:
                frame_data["scale_changed"] = True
                base_p = name
                img_data["name"] = name
                
                img_data["img_info"] = img_info

                frame_data["selected_file"]["idx"] = i
                frame_data["selected_file"]["name"] = base_p
            if frame_data["scale_changed"]:
                frame_data["scale_changed"] = False
                img_info.change_scale(frame_data["img_scale"])

            if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [img_info.w, img_info.h]

            frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [img_info.scaled_w, img_info.scaled_h]
                     

    imgui.end_child()
    imgui.same_line()

def _handle_bbox_drag(frame_data, labeling, img_info: ImageInfo):
    if imgui.is_mouse_down() and labeling["curr_bbox"] is not None:

        mouse_pos_x = frame_data["io"].mouse_pos[0]
        mouse_pos_y = frame_data["io"].mouse_pos[1]
        if not labeling["was_drawing"]:
            labeling["was_drawing"] = True
            # save relative mouse offset
            labeling["x_offset"] = labeling["curr_bbox"].width - ( labeling["curr_bbox"].xmax + frame_data["x_offset"] - mouse_pos_x  )  
            labeling["y_offset"] = labeling["curr_bbox"].height - (labeling["curr_bbox"].ymax - mouse_pos_y + frame_data["y_offset"] - imgui.get_scroll_y()) 

        mouse_pos_x -= labeling["x_offset"]
        mouse_pos_y -= labeling["y_offset"]

        labeling["curr_bbox"].xmin = mouse_pos_x - frame_data["x_offset"] # - labeling["curr_bbox"]["width"]/2 # frame_data["io"].mouse_pos[0] ) - labeling["curr_bbox"]["x_min"] ) #  
        labeling["curr_bbox"].ymin = mouse_pos_y + imgui.get_scroll_y() - frame_data["y_offset"]  #frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"] - labeling["curr_bbox"]["height"]/2 # -(labeling["curr_bbox"]["y_max"] - frame_data["io"].mouse_pos[1] )  #
        labeling["curr_bbox"].xmax = labeling["curr_bbox"].xmin + labeling["curr_bbox"].width
        labeling["curr_bbox"].ymax = labeling["curr_bbox"].ymin + labeling["curr_bbox"].height

        img_info.set_changed(True)
    else:
        labeling["was_drawing"] = False


def _handle_bbox_resize(frame_data, labeling, img_info: ImageInfo):
    if imgui.is_mouse_down(1) and labeling["curr_bbox"] is not None:

        labeling["curr_bbox"].xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"]
        labeling["curr_bbox"].ymax = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"]
        labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin)
        labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)
        img_info.set_changed(True)

def _update_selected_bbox(frame_data, labeling, project: Project, draw_list):
    found = []
    img_data = frame_data["imgs_to_render"]["annotate_preview"]
    img_info : ImageInfo = img_data["img_info"]

    for bbox in img_info.bboxes:
        
        draw_list.add_rect(
            bbox.xmin + frame_data["x_offset"], 
            bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"], 
            bbox.xmax + frame_data["x_offset"], 
            bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"], 
            imgui.get_color_u32_rgba(*project.labels.labels_map[bbox.label].rgb, 255),
            thickness=1
        )

        if imgui.get_mouse_pos()[0] >= bbox.xmin + frame_data["x_offset"]  and\
            imgui.get_mouse_pos()[0] <= bbox.xmax + frame_data["x_offset"]  and\
            imgui.get_mouse_pos()[1] >= bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"]  and\
            imgui.get_mouse_pos()[1] <=  bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"] :
            
            if frame_data["prev_cursor"] != glfw.HAND_CURSOR:
                glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.HAND_CURSOR))
                frame_data["prev_cursor"] = glfw.HAND_CURSOR
                #print("created")
            found.append(bbox)
            
    # take the closest window. Needed for nested bboxes.
    ordered_found = sorted(found, key=lambda x: abs(imgui.get_mouse_pos()[0] - x.xmin))

    if len(ordered_found) > 0 and labeling["curr_bbox"] is None:
        labeling["curr_bbox"] = ordered_found[0]
    if frame_data["prev_cursor"] != glfw.ARROW_CURSOR and found == [] and not imgui.is_mouse_down(1):
        frame_data["prev_cursor"] = glfw.ARROW_CURSOR
        glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.ARROW_CURSOR))

def _annotation_screen():
    global frame_data
    img_data = frame_data["imgs_to_render"]["annotate_preview"]

    img_info : ImageInfo = img_data["img_info"]
    labeling = frame_data["labeling"]
    project : Project = frame_data["project"]

    imgui.begin_child(label="img_preview", width=-1, height=-1, border=False,)
    if img_data["texture"] is not None:
        imgui.image(img_data["texture"], img_data["scaled_width"], img_data["scaled_height"])
    
    draw_list = imgui.get_window_draw_list()

    # new bbox requested, was drawing a box and mouse is released => save bbox
    if not imgui.is_mouse_down() and labeling["was_mouse_down"] and labeling["new_box_requested"]:
        labeling["was_mouse_down"] = False
        labeling["new_box_requested"] = False
        labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin)
        labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)

        img_info.bboxes.append(deepcopy(labeling["curr_bbox"]))
        if labeling["curr_bbox"] is not None:
            labeling["curr_bbox"] = None
        img_info.set_changed(True)
    # draw bbox following mouse coords
    elif imgui.is_mouse_down() and labeling["new_box_requested"]:

        labeling["was_mouse_down"] = True
        curr_bbox : BBox = labeling["curr_bbox"]
        if curr_bbox is None:
            # save coords relative to the image
            curr_bbox = BBox(
                frame_data["io"].mouse_pos[0] - frame_data["x_offset"],
                frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"],
                0,
                0,
                frame_data["labeling"]["selected_label"]
            )
            labeling["curr_bbox"] = curr_bbox
        
        curr_bbox.xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"]
        curr_bbox.ymax = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"]
        # convert image coords to screen coords
        draw_list.add_rect(
            curr_bbox.xmin + frame_data["x_offset"], 
            curr_bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"], 
            curr_bbox.xmax + frame_data["x_offset"], 
            curr_bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"], 
            imgui.get_color_u32_rgba(*project.labels.labels_map[curr_bbox.label].rgb, 255), 
            thickness=1)
        img_info.set_changed(True)
    else: # draw bboxes and handle interaction
        
        if img_data["img_info"] is not None:
            _update_selected_bbox(frame_data, labeling, project, draw_list)
            
        _handle_bbox_drag(frame_data, labeling,img_info)
        _handle_bbox_resize(frame_data, labeling,img_info)
        
        # remove bbox shortcut
        if imgui.is_key_pressed(glfw.KEY_BACKSPACE) and labeling["curr_bbox"] is not None:
            img_info.bboxes.remove(labeling["curr_bbox"])
            labeling["curr_bbox"] = None
            img_info.set_changed(True)

        for i in project.labels.shortcuts:
            if imgui.is_key_pressed(int(i)+glfw.KEY_0) :
                frame_data["labeling"]["selected_label"] = project.labels.shortcuts[i].index
                if labeling["curr_bbox"] is not None:
                    labeling["curr_bbox"].label = project.labels.shortcuts[i].index
                    img_info.set_changed(True)
                break

        if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1):
            labeling["curr_bbox"] = None
    imgui.end_child()