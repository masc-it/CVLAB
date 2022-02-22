import imgui
from components.data import BBox, ImageInfo, Labels
from variables import frame_data
import threading

from .file_selector import file_selector
from auto_annotation import header_auto_annotation, auto_ann_content
import glfw
from copy import deepcopy
from .projects import Project


def header():
    global frame_data
    
    if imgui.begin_tab_bar("sections"):

        if imgui.begin_tab_item("LAB")[0]:

            header_lab()
            lab_content()
            imgui.end_tab_item()
        
        if imgui.begin_tab_item("Auto annotation")[0]:
            header_auto_annotation()
            auto_ann_content()
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


def lab_content():
    _files_list("annotate_preview")
    _annotation_screen("annotate_preview")


def _files_list(img_render_id):
    global frame_data
    project : Project = frame_data["project"]
    img_data = frame_data["imgs_to_render"][img_render_id]
    
    # add 20 more (scrollbar)
    frame_data["x_offset"] = int(frame_data["viewport"][0] / 5) + 20

    imgui.begin_child(label="files_list", width=frame_data["x_offset"] - 20, height=-1, border=False, )
    
    for collection_id in project.collections:

        if imgui.tree_node(project.collections[collection_id].name):
            for i, img_info in enumerate(project.get_image(collection_id)):

                # img_info = project.imgs[k]
                name = img_info.name
                clicked, _ = imgui.selectable(
                            label=name, selected=(frame_data["selected_file"]["idx"] == i and frame_data["selected_file"]["collection"] == collection_id)
                        )
                
                if clicked or frame_data["scale_changed"]:
                    
                    img_data["scale"] = frame_data["img_scale"]
                    if clicked:
                        frame_data["scale_changed"] = True
                        base_p = name
                        img_data["name"] = name
                        
                        img_data["img_info"] = img_info
                        frame_data["selected_file"]["collection"] = collection_id
                        frame_data["selected_file"]["idx"] = i
                        frame_data["selected_file"]["name"] = base_p
                    if frame_data["scale_changed"]:
                        frame_data["scale_changed"] = False
                        img_data["img_info"].change_scale(frame_data["img_scale"])
                        
                    if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                        frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                        frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [img_data["img_info"].w, img_data["img_info"].h]

                    frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [img_data["img_info"].scaled_w, img_data["img_info"].scaled_h]
            imgui.tree_pop()
                        
    imgui.end_child()
    imgui.same_line(position=frame_data["x_offset"])

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

def _refresh_bboxes(labeling, project: Project, draw_list, img_render_id):
    found = []
    global frame_data
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

def _annotation_screen(img_render_id, allow_edit=True):
    global frame_data
    img_data = frame_data["imgs_to_render"][img_render_id]

    img_info : ImageInfo = img_data["img_info"]
    labeling = frame_data["labeling"]
    project : Project = frame_data["project"]

    imgui.begin_child(label="img_preview", width=0, height=0, border=False,)
    if img_data["texture"] is not None:
        imgui.image(img_data["texture"], img_data["scaled_width"], img_data["scaled_height"])
    
    draw_list = imgui.get_window_draw_list()

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
            _refresh_bboxes(labeling, project, draw_list, img_render_id)
        
        if allow_edit:
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