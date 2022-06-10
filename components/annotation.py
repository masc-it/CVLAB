import imgui
from .data import *
from .projects import Project
import glfw

MIN_BBOX_SIZE = 5

def _annotation_screen(frame_data, img_render_id, allow_edit=True):

    img_data = frame_data["imgs_to_render"][img_render_id]

    img_info : ImageInfo = img_data["img_info"]
    labeling = frame_data["labeling"]
    project : Project = frame_data["project"]
    """ print( "pos: " + str(imgui.get_mouse_pos()))
    print("vp: " + str(imgui.get_main_viewport().size))
    print( "avail: " + str(imgui.get_content_region_available())) """
    
    imgui.begin_child(label="img_preview", width=0, height=0, border=False,)
    frame_data["y_offset"] = imgui.get_main_viewport().size.y - imgui.get_content_region_available().y - 8 # frame_data["y_offset_auto_ann"]
    if img_data["texture"] is not None:
        imgui.image(img_data["texture"], img_data["scaled_width"], img_data["scaled_height"])
    draw_list : imgui._DrawList = imgui.get_window_draw_list()
    
    # new bbox requested, was drawing a box and mouse is released => save bbox
    if allow_edit and not imgui.is_mouse_down() and labeling["was_mouse_down"] and labeling["new_box_requested"]:
        labeling["was_mouse_down"] = False
        labeling["new_box_requested"] = False
        labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin)
        labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)

        img_info.bboxes.append(labeling["curr_bbox"])
        if labeling["curr_bbox"] is not None:
            labeling["curr_bbox"] = None
        img_info.set_changed(True)
    # draw bbox following mouse coords
    elif allow_edit and imgui.is_mouse_down() and labeling["new_box_requested"]:

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

        # prevent to draw boxes right-2-left
        __check_bbox(curr_bbox, frame_data, img_info)

        if curr_bbox.xmax - curr_bbox.xmin > MIN_BBOX_SIZE and\
           curr_bbox.ymax - curr_bbox.ymin > MIN_BBOX_SIZE : # bboxes must have at least 5px width/height
            draw_list.add_rect(
                curr_bbox.xmin + frame_data["x_offset"], 
                curr_bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"], 
                curr_bbox.xmax + frame_data["x_offset"], 
                curr_bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"], 
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
                if imgui.is_key_pressed(int(i)+glfw.KEY_0) :
                    frame_data["labeling"]["selected_label"] = project.labels.shortcuts[i].index
                    if labeling["curr_bbox"] is not None:
                        labeling["curr_bbox"].label = project.labels.shortcuts[i].index
                        img_info.set_changed(True)
                    break

            if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1):
                labeling["curr_bbox"] = None
    imgui.end_child()


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
    if labeling["curr_bbox"] is not None and img_info is not None and imgui.is_mouse_down():

        mouse_pos_x = frame_data["io"].mouse_pos[0]
        mouse_pos_y = frame_data["io"].mouse_pos[1]
        if not labeling["was_drawing"]:
            labeling["was_drawing"] = True
            # save relative mouse offset
            labeling["x_offset"] = labeling["curr_bbox"].width - ( labeling["curr_bbox"].xmax + frame_data["x_offset"] - mouse_pos_x  )  
            labeling["y_offset"] = labeling["curr_bbox"].height - (labeling["curr_bbox"].ymax - mouse_pos_y + frame_data["y_offset"] - imgui.get_scroll_y()) 
 
        mouse_pos_x -= labeling["x_offset"]
        mouse_pos_y -= labeling["y_offset"]

        new_xmin = mouse_pos_x - frame_data["x_offset"]
        if new_xmin >= 0 and new_xmin + labeling["curr_bbox"].width < img_info.scaled_w:
            labeling["curr_bbox"].xmin = max(0, new_xmin)
        
        new_xmax = labeling["curr_bbox"].xmin + labeling["curr_bbox"].width
        if new_xmax <= img_info.scaled_w:
            labeling["curr_bbox"].xmax = min(img_info.scaled_w, new_xmax)

        new_ymin = mouse_pos_y + imgui.get_scroll_y() - frame_data["y_offset"]

        if new_ymin >= 0 and new_ymin + labeling["curr_bbox"].height < img_info.scaled_h:        
            labeling["curr_bbox"].ymin = max(0, new_ymin)  #frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"] - labeling["curr_bbox"]["height"]/2 # -(labeling["curr_bbox"]["y_max"] - frame_data["io"].mouse_pos[1] )  #
        
        labeling["curr_bbox"].ymax = min(img_info.scaled_h, labeling["curr_bbox"].ymin + labeling["curr_bbox"].height)
    
        img_info.set_changed(True)
    else:
        labeling["was_drawing"] = False


def _handle_bbox_resize(frame_data, labeling, img_info: ImageInfo):
    if imgui.is_mouse_down(1) and labeling["curr_bbox"] is not None:

        labeling["curr_bbox"].xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"]
        labeling["curr_bbox"].ymax = frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"]
        
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
        
        draw_list.add_rect(
            bbox.xmin + frame_data["x_offset"], 
            bbox.ymin - imgui.get_scroll_y() +  frame_data["y_offset"], 
            bbox.xmax + frame_data["x_offset"], 
            bbox.ymax - imgui.get_scroll_y() +  frame_data["y_offset"], 
            imgui.get_color_u32_rgba(*project.labels.labels_map[bbox.label].rgb, 255),
            thickness=1
        )

        if not frame_data["is_dialog_open"] and imgui.get_mouse_pos()[0] >= bbox.xmin + frame_data["x_offset"]  and\
            imgui.get_mouse_pos()[0] <= bbox.xmax + frame_data["x_offset"]  and\
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
