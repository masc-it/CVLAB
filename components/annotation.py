from pathlib import Path
from threading import Thread
import imgui
from .data import *
from .projects import Project
import glfw
import numpy as np
from yolov5 import detect
from .modals import show_label_selection
import time

from autoannotate_utils.unsupervised_classification import PseudoClassifier

MIN_BBOX_SIZE = 5

def _annotation_screen(frame_data, img_render_id, allow_edit=True):

    img_data = frame_data["imgs_to_render"][img_render_id]

    img_info : ImageInfo = img_data["img_info"]
    labeling = frame_data["labeling"]
    project : Project = frame_data["project"]
    """ print( "pos: " + str(imgui.get_mouse_pos()))
    print("vp: " + str(imgui.get_main_viewport().size))
    print( "avail: " + str(imgui.get_content_region_available())) """
    
    imgui.begin_child(label="img_preview", width=0, height=0, border=False, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR )
    
    padding = 8

    if img_data["texture"] is not None and img_data["scaled_width"] > imgui.get_content_region_available().x:
        padding = 22 # 8 + 14 = h_scrollbar height
    
    frame_data["y_offset"] = imgui.get_main_viewport().size.y - imgui.get_content_region_available().y - padding # frame_data["y_offset_auto_ann"]
    if img_data["texture"] is not None:
        imgui.image(img_data["texture"], img_data["scaled_width"], img_data["scaled_height"])
    draw_list : imgui._DrawList = imgui.get_window_draw_list()
    
    if img_data["texture"] is not None and frame_data["is_editing"] == False and (frame_data["io"].mouse_pos[0] <= frame_data["x_offset"] or \
       frame_data["io"].mouse_pos[1] <= frame_data["y_offset"] or frame_data["io"].mouse_pos[1] >= img_data["scaled_height"] + frame_data["y_offset"]) :
        labeling["was_mouse_down"] = False
        labeling["new_box_requested"] = False
        labeling["curr_bbox"] = None
    # new bbox requested, was drawing a box and mouse is released => save bbox
    if labeling["curr_bbox"] is not None and frame_data["is_editing"] == False and allow_edit and labeling["was_mouse_down"] and labeling["new_box_requested"] and not imgui.is_mouse_down() :
        labeling["was_mouse_down"] = False
        #labeling["new_box_requested"] = False
        labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin)
        labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)

        if frame_data["autoannotate"] == True:
            autoannotate(frame_data, labeling["curr_bbox"], img_info)
        else:
            img_info.bboxes.append(labeling["curr_bbox"])
            img_info.set_changed(True)
            #if labeling["curr_bbox"] is not None:
        
        auto_classify(frame_data, labeling["curr_bbox"], img_info)
        if frame_data["autoclassifier"] != -1:
            labeling["curr_bbox"].label = frame_data["autoclassifier"]
            frame_data["autoclassifier"] = -1
        
        labeling["curr_bbox"] = None
        if frame_data["autoannotate"]:
            frame_data["autoannotate"] = False
            labeling["new_box_requested"] = False
            
    # draw bbox following mouse coords
    elif allow_edit and not frame_data["is_dialog_open"] and imgui.is_mouse_down() and labeling["new_box_requested"]:

        labeling["was_mouse_down"] = True
        curr_bbox : BBox = labeling["curr_bbox"]
        if curr_bbox is None:
            # save coords relative to the image, not app 
            curr_bbox = BBox(
                frame_data["io"].mouse_pos[0] - frame_data["x_offset"] + imgui.get_scroll_x(),
                frame_data["io"].mouse_pos[1] - frame_data["y_offset"] + imgui.get_scroll_y(),
                0,
                0,
                frame_data["labeling"]["selected_label"]
            )
            labeling["curr_bbox"] = curr_bbox
        
        curr_bbox.xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"] + imgui.get_scroll_x()
        curr_bbox.ymax = frame_data["io"].mouse_pos[1] - frame_data["y_offset"] + imgui.get_scroll_y() 
        # convert image coords to screen coords

        # prevent to draw boxes right-2-left
        __check_bbox(curr_bbox, frame_data, img_info)

        if curr_bbox.xmax - curr_bbox.xmin > MIN_BBOX_SIZE and\
           curr_bbox.ymax - curr_bbox.ymin > MIN_BBOX_SIZE : # bboxes must have at least 5px width/height
            draw_list.add_rect(
                curr_bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x(), 
                curr_bbox.ymin +  frame_data["y_offset"] - imgui.get_scroll_y() , 
                curr_bbox.xmax + frame_data["x_offset"] - imgui.get_scroll_x(), 
                curr_bbox.ymax  +  frame_data["y_offset"] - imgui.get_scroll_y(), 
                imgui.get_color_u32_rgba(*project.labels.labels_map[curr_bbox.label].rgb, 255), 
                thickness=1)
            img_info.set_changed(True)
    else: # draw bboxes and handle interaction
        
        if img_info is not None:
            
            _refresh_bboxes(frame_data, labeling, project, draw_list, img_render_id)
        
        if allow_edit and not frame_data["is_dialog_open"]:
            _handle_bbox_drag(frame_data, labeling,img_info)
            _handle_bbox_resize(frame_data, labeling,img_info)
            
            # remove bbox shortcut
            if imgui.is_key_pressed(glfw.KEY_BACKSPACE) and labeling["curr_bbox"] is not None:
                img_info.bboxes.remove(labeling["curr_bbox"])
                labeling["curr_bbox"] = None
                img_info.set_changed(True)            
                
            for i in project.labels.shortcuts:
                if i == "":
                    continue
                if imgui.is_key_pressed(int(i)+glfw.KEY_0) : 
                    frame_data["labeling"]["selected_label"] = project.labels.shortcuts[i].index
                    if labeling["curr_bbox"] is not None:
                        labeling["curr_bbox"].label = project.labels.shortcuts[i].index
                        img_info.set_changed(True)
                    break
            
            if labeling["curr_bbox"] is not None:
                l = project.labels.labels_map[labeling['curr_bbox'].label].label
                imgui.set_tooltip(f"Label: {l}")

            if imgui.is_key_pressed(glfw.KEY_TAB) and labeling["curr_bbox"] is not None:
                
                imgui.open_popup("Label")
                imgui.set_next_window_size(350, 600)
                frame_data["is_editing"] = True
                frame_data["is_dialog_open"] = True
            
            """ if imgui.is_key_pressed(glfw.KEY_C) and labeling["curr_bbox"] is not None:
                auto_classify(frame_data, labeling["curr_bbox"], img_info) """
            
            # duplicate bbox
            if imgui.is_key_pressed(glfw.KEY_D) and labeling["curr_bbox"] is not None:
                
                labeling["new_box_requested"] = False
                xmin = labeling["curr_bbox"].xmax + 3
                xmax = xmin + labeling["curr_bbox"].width

                bbox_copy = BBox(
                    xmin,
                    labeling["curr_bbox"].ymin,
                    xmax,
                    labeling["curr_bbox"].ymax,
                    labeling["curr_bbox"].label
                )
                img_info.bboxes.append(bbox_copy)
            
            if imgui.is_key_pressed(glfw.KEY_SPACE) and labeling["curr_bbox"] is not None:
                auto_classify(frame_data, labeling["curr_bbox"], img_info)
                if frame_data["autoclassifier"] != -1:
                    labeling["curr_bbox"].label = frame_data["autoclassifier"]
                    frame_data["autoclassifier"] = -1

            if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1) and frame_data["is_dialog_open"] == False and frame_data["is_editing"] == False:
                labeling["curr_bbox"] = None
        
        show_label_selection(frame_data, labeling["curr_bbox"], img_info)
        
    imgui.end_child()


def add_bboxes_to_kb(frame_data, img_info: ImageInfo):

    img_info_path = Path(img_info.path)
    classifier : PseudoClassifier = frame_data["classifier"]
    img = Image.open(img_info_path).convert("RGB")

    for i, bbox in enumerate(img_info.bboxes):
        random_name = f"{img_info_path.stem}_{i}"
        crop_path = (classifier.kb_path / "imgs" / random_name ).with_suffix(".jpg")

        if crop_path.exists():
            continue
        scaled_bbox = bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h))
        crop = img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax)))
        
        crop.save(crop_path)

        classifier.add_img_to_kb( img_info_path, crop_path, bbox.label)

    classifier.save_kb_single(img_info_path.stem)
    print("kb saved")

def auto_classify(frame_data, bbox: BBox, img_info: ImageInfo ):

    classifier : PseudoClassifier = frame_data["classifier"]
    img = Image.open(img_info.path).convert("RGB")
    scaled_bbox = bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h))
    crop = img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax)))
    
    """ random_name = f"{round(time.time()*1000)}"
    crop_path = (classifier.kb_path / random_name ).with_suffix(".jpg")
    crop.save(crop_path) """

    label, _, _ = classifier.predict_label(img_path=crop)
    if label is not None:
        frame_data["autoclassifier"] = label
        print(frame_data["project"].labels.labels_map[str(label)].label)
    else:
        frame_data["autoclassifier"] = -1

def get_iou(bbox1:BBox, bbox2: BBox):
        """
        Calculate the Intersection over Union (IoU) of two bounding boxes.

        Returns
        -------
        float
            in [0, 1]
        """

        # determine the coordinates of the intersection rectangle
        x_left = max(bbox1.xmin, bbox2.xmin)
        y_top = max(bbox1.ymin, bbox2.ymin)
        x_right = min(bbox1.xmax, bbox2.xmax)
        y_bottom = min(bbox1.ymax, bbox2.ymax)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        # The intersection of two axis-aligned bounding boxes is always an
        # axis-aligned bounding box
        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # compute the area of both AABBs
        bb1_area = (bbox1.xmax - bbox1.xmin) * (bbox1.ymax - bbox1.ymin)
        bb2_area = (bbox2.xmax - bbox2.xmin) * (bbox2.ymax - bbox2.ymin)

        # compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the interesection area
        iou = intersection_area / float(bb1_area + bb2_area - intersection_area)

        return iou
def start_autoann(frame_data, img_info: ImageInfo, img_path: Path):
    
    predictions = detect.run(weights="D:/Download/letters_best0207.pt", imgsz=[1280, 1090], conf_thres=0.1, iou_thres=0.5, save_conf=True,
                exist_ok=True, save_txt=False, source=img_path, project=None, name=None,)

    for _, (bboxes, img)  in enumerate(predictions):
        
        #print(bboxes)
        # exp.imgs.append(img_info)
        for bbox in bboxes:
            bbox : BBox = BBox(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"], bbox["class"], bbox["conf"])

            if img_info.scale != 1:
                bbox = bbox.scale((img_info.orig_w, img_info.orig_h), (img_info.scaled_w, img_info.scaled_h))

            same = list(filter(lambda x: x.xmin == bbox.xmin and x.ymin == bbox.ymin or ( bbox.xmin > x.xmin and bbox.ymin > x.ymin and bbox.xmax < x.xmax and bbox.ymax < x.ymax ) or ( bbox.xmin < x.xmin and bbox.ymin < x.ymin and bbox.xmax > x.xmax and bbox.ymax > x.ymax ) or get_iou(bbox, x) > 0.6, img_info.bboxes))
            if len(same) == 0:
                img_info.add_bbox(bbox)
            else:
                same.append(bbox)
                same = list(sorted(same, key= lambda x: x.conf, reverse=True))

                for d in same[1:]:
                    img_info.bboxes.remove(d)
                
                img_info.bboxes.append(same[0])


def autoannotate(frame_data, bbox: BBox, img_info: ImageInfo):
    # load image
    img = Image.open(img_info.path).convert("RGB")

    # mask area outside selected bbox
    arr = np.zeros((img.size[1], img.size[0], 3))
    scaled_bbox = bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h))
    crop = np.array(img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax))))
    arr[math.ceil(scaled_bbox.ymin):math.ceil(scaled_bbox.ymax), math.ceil(scaled_bbox.xmin):math.ceil(scaled_bbox.xmax), ...] = crop
    
    img = Image.fromarray(np.uint8(arr))
    img.save("lmao.jpg")
    # run predictions

    t = Thread(target=(start_autoann), args=(frame_data, img_info, Path("lmao.jpg") ))
    t.start()
    # add bboxes to canvas
    

def __check_bbox(bbox : BBox, frame_data :dict, img_info: ImageInfo):
    # prevent to draw boxes right-2-left
    if bbox.xmin > bbox.xmax:
        xmin = bbox.xmax
        bbox.xmax = bbox.xmin
        bbox.xmin = xmin
    
    if bbox.ymin > bbox.ymax:
        ymin = bbox.ymax
        bbox.ymax = bbox.ymin
        bbox.ymin = ymin
 
    #print(bbox.as_array())
    bbox.xmin = max(0, bbox.xmin)
    bbox.ymin = max(0, bbox.ymin)

    bbox.xmax = min(img_info.scaled_w, bbox.xmax)
    bbox.ymax = min(img_info.scaled_h, bbox.ymax)

    if bbox.xmax - bbox.xmin <= MIN_BBOX_SIZE:
        bbox.xmax = bbox.xmin + MIN_BBOX_SIZE
    if bbox.ymax - bbox.ymin <= MIN_BBOX_SIZE:
        bbox.ymax = bbox.ymin + MIN_BBOX_SIZE
    bbox.update_size()
    #print(bbox.as_array())


def _handle_bbox_drag(frame_data, labeling, img_info: ImageInfo):
    if labeling["curr_bbox"] is not None and img_info is not None and\
       frame_data["io"].mouse_pos[0] < frame_data["viewport"][0] - frame_data["scroll_right_margin"] and imgui.is_mouse_down():

        mouse_pos_x = frame_data["io"].mouse_pos[0]
        mouse_pos_y = frame_data["io"].mouse_pos[1]
        if not labeling["was_drawing"]:
            labeling["was_drawing"] = True
            # save relative mouse offset
            labeling["x_offset"] = labeling["curr_bbox"].width - ( labeling["curr_bbox"].xmax + frame_data["x_offset"] - imgui.get_scroll_x() - mouse_pos_x  )  
            labeling["y_offset"] = labeling["curr_bbox"].height - (labeling["curr_bbox"].ymax - mouse_pos_y + frame_data["y_offset"] - imgui.get_scroll_y()) 
 
        mouse_pos_x -= labeling["x_offset"]
        mouse_pos_y -= labeling["y_offset"]

        new_xmin = mouse_pos_x - frame_data["x_offset"] + imgui.get_scroll_x()
        if new_xmin >= 0 and new_xmin + labeling["curr_bbox"].width < img_info.scaled_w:
            labeling["curr_bbox"].xmin = max(0, new_xmin)
        
        new_xmax = labeling["curr_bbox"].xmin + labeling["curr_bbox"].width
        if new_xmax <= img_info.scaled_w:
            labeling["curr_bbox"].xmax = min(img_info.scaled_w, new_xmax)

        new_ymin = mouse_pos_y - frame_data["y_offset"] + imgui.get_scroll_y() 

        if new_ymin >= 0 and new_ymin + labeling["curr_bbox"].height < img_info.scaled_h:        
            labeling["curr_bbox"].ymin = max(0, new_ymin)  #frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"] - labeling["curr_bbox"]["height"]/2 # -(labeling["curr_bbox"]["y_max"] - frame_data["io"].mouse_pos[1] )  #
        
        labeling["curr_bbox"].ymax = min(img_info.scaled_h, labeling["curr_bbox"].ymin + labeling["curr_bbox"].height)
    
        img_info.set_changed(True)
    else:
        labeling["was_drawing"] = False


def is_mouse_on_bbox_border(bbox: BBox, frame_data):

    if (frame_data["io"].mouse_pos[0] - frame_data["x_offset"] <= bbox.xmax and frame_data["io"].mouse_pos[0] - frame_data["x_offset"] >= bbox.xmax - 5) or\
        (frame_data["io"].mouse_pos[1]  + imgui.get_scroll_y() - frame_data["y_offset"] <= bbox.ymax and frame_data["io"].mouse_pos[1]  + imgui.get_scroll_y() - frame_data["y_offset"] >= bbox.ymax - 5) :
        print("on border")
        frame_data["can_resize"] = True


def _handle_bbox_resize(frame_data, labeling, img_info: ImageInfo):

    # TODO 
    #if labeling["curr_bbox"] is not None:
    #    is_mouse_on_bbox_border( labeling["curr_bbox"], frame_data)
    if imgui.is_mouse_down(1) and labeling["curr_bbox"] is not None:

        labeling["curr_bbox"].xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"] + imgui.get_scroll_x()
        labeling["curr_bbox"].ymax = frame_data["io"].mouse_pos[1] - frame_data["y_offset"] + imgui.get_scroll_y()
        
        # prevent to draw boxes right-2-left
        __check_bbox(labeling["curr_bbox"], frame_data, img_info)
        
        labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin) 
        labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)

        img_info.set_changed(True)

def _refresh_bboxes(frame_data, labeling, project: Project, draw_list, img_render_id):
    found = []
    img_data = frame_data["imgs_to_render"][img_render_id]
    img_info : ImageInfo = img_data["img_info"]

    for bbox in img_info.bboxes:
        
        # convert to app coordinates
        draw_list.add_rect(
            bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x(), 
            bbox.ymin +  frame_data["y_offset"] - imgui.get_scroll_y(), 
            bbox.xmax + frame_data["x_offset"] - imgui.get_scroll_x(), 
            bbox.ymax +  frame_data["y_offset"] - imgui.get_scroll_y() , 
            imgui.get_color_u32_rgba(*project.labels.labels_map[bbox.label].rgb, 255),
            thickness=1
        )

        draw_list.add_rect_filled(
            bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x(), 
            bbox.ymin - 12 +  frame_data["y_offset"] - imgui.get_scroll_y(), 
            bbox.xmax + frame_data["x_offset"] - imgui.get_scroll_x(), 
            bbox.ymin  +  frame_data["y_offset"] - imgui.get_scroll_y(), 
            imgui.get_color_u32_rgba(*project.labels.labels_map[bbox.label].rgb, 255)
        )

        imgui.set_cursor_screen_pos(
            (bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x(),
            bbox.ymin - 14 - imgui.get_scroll_y() +  frame_data["y_offset"]
            )
        )
        imgui.text(
            project.labels.labels_map[bbox.label].label[:3]
        )

        if not frame_data["is_dialog_open"] and imgui.get_mouse_pos()[0] >= bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x() and\
            imgui.get_mouse_pos()[0] <= bbox.xmax + frame_data["x_offset"] - imgui.get_scroll_x() and\
            imgui.get_mouse_pos()[1] >= bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"]  and\
            imgui.get_mouse_pos()[1] <=  bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"] :
            
            if frame_data["prev_cursor"] != glfw.HAND_CURSOR:
                glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.HAND_CURSOR))
                frame_data["prev_cursor"] = glfw.HAND_CURSOR
                #print("created")
            found.append(bbox)
    
    if frame_data["is_dialog_open"]:
        return
    # take the closest window. Needed for nested bboxes.
    ordered_found = sorted(found, key=lambda x: abs(imgui.get_mouse_pos()[0] - x.xmin))

    if len(ordered_found) > 0 and labeling["curr_bbox"] is None:
        labeling["curr_bbox"] = ordered_found[0]
    if frame_data["prev_cursor"] != glfw.ARROW_CURSOR and found == [] and not imgui.is_mouse_down(1):
        frame_data["prev_cursor"] = glfw.ARROW_CURSOR
        glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.ARROW_CURSOR))
    
