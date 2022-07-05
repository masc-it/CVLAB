import imgui
from components.data import ImageInfo
from variables import frame_data
from .auto_annotation import header_auto_annotation, auto_ann_content
import glfw
from ..model.project import Project
from . import annotation, settings

def header():
    global frame_data
    
    if imgui.begin_tab_bar("sections"):

        if imgui.begin_tab_item("LAB")[0]:

            frame_data["y_offset"] = frame_data["y_offset_lab"]
            header_lab()
            lab_content()
            imgui.end_tab_item()
        
        if imgui.begin_tab_item("Auto annotation")[0]:
            #print(imgui.get_mouse_pos())
            #frame_data["y_offset"] = imgui.get_main_viewport().size.y - imgui.get_content_region_available().y - 8 # frame_data["y_offset_auto_ann"]
            
            header_auto_annotation(frame_data)
            auto_ann_content(frame_data)
            
            imgui.end_tab_item()
        
        if imgui.begin_tab_item("Settings & Info")[0]:

            project : Project = frame_data["project"]
            imgui.begin_child(label="setting_section", border=False, )
            settings.settings_labels(project.labels)
            settings.settings_dd()
            settings.settings_label_distribution()
            imgui.end_child()
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

    autoannotate_click = imgui.button("Auto annotate" if not frame_data["autoannotate"] else "Draw box")
    if imgui.is_key_pressed(glfw.KEY_A):
        if labeling["new_box_requested"] == False:
            labeling["new_box_requested"] = (not labeling["new_box_requested"])
        frame_data["autoannotate"] = (not frame_data["autoannotate"])
    imgui.same_line()

    autoclassify_click = imgui.button("Add boxes to KB")
    if autoclassify_click:
        img_data = frame_data["imgs_to_render"]["annotate_preview"]

        img_info : ImageInfo = img_data["img_info"]
        annotation.add_bboxes_to_kb(frame_data, img_info)

    imgui.same_line()
    
    scale_changed, frame_data["img_scale"] = imgui.slider_float(
                label="Zoom",
                value=frame_data["img_scale"],
                min_value=0.5,
                max_value=4.0,
                format="%.1f",
            )
    if scale_changed:
        frame_data["scale_changed"] = True
    
    if frame_data["io"].mouse_pos[0] > frame_data["viewport"][0] - frame_data["scroll_right_margin"]:
        #frame_data["prev_cursor"] = glfw.ARROW_CURSOR
        glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(glfw.VRESIZE_CURSOR))
    else:
        glfw.set_cursor(frame_data["glfw"]["window"], glfw.create_standard_cursor(frame_data["prev_cursor"]))

    mouse_wheel = frame_data["io"].mouse_wheel
    if frame_data["is_dialog_open"] == False and mouse_wheel != 0 and frame_data["io"].mouse_pos[0] > frame_data["x_offset"] and\
        frame_data["io"].mouse_pos[0] < frame_data["viewport"][0] - frame_data["scroll_right_margin"]:
        frame_data["img_scale"] += 0.2 if mouse_wheel > 0 else -0.2
        frame_data["img_scale"] = min(4.0, frame_data["img_scale"])
        frame_data["img_scale"] = max(0.5, frame_data["img_scale"])
        frame_data["scale_changed"] = True
    


def lab_content():
    global frame_data
    _files_list(frame_data, "annotate_preview")
    annotation._annotation_screen(frame_data, "annotate_preview")


def _files_list(frame_data, img_render_id):
    project : Project = frame_data["project"]
    img_data = frame_data["imgs_to_render"][img_render_id]
    
    padding = 20
    # add 20 more (scrollbar)
    frame_data["x_offset"] = int(frame_data["viewport"][0] / 5) + padding
    
    imgui.begin_child(label="files_list", width=frame_data["x_offset"] - padding, height=-1, border=False, )
    
    for collection_id in project.collections:

        collection_open = imgui.tree_node(project.collections[collection_id].name)
        if imgui.is_item_hovered():
            dd_info, _ = project.get_data_distribution()
            imgui.set_tooltip(f"Num. samples: {dd_info[project.collections[collection_id].name]['tot']}\nSplit Ratio: {dd_info[project.collections[collection_id].name]['ratio']:.2f}%")
        
        if collection_open:
            imgs = project.get_images(collection_id)
            key_pressed = 0

            if imgui.is_key_pressed(glfw.KEY_DOWN):
                
                key_pressed = 1
            
            if imgui.is_key_pressed(glfw.KEY_UP):
                key_pressed = -1
            
            if key_pressed != 0:

                frame_data["selected_file"]["idx"] += key_pressed

                if frame_data["selected_file"]["idx"] == len(imgs) - 1:
                    frame_data["selected_file"]["idx"] = 0
                elif frame_data["selected_file"]["idx"] < 0:
                    frame_data["selected_file"]["idx"] = 0
                
                
                img_i = imgs[frame_data["selected_file"]["idx"]]

                name = img_i.name
                img_data["scale"] = frame_data["img_scale"]

                frame_data["scale_changed"] = True
                base_p = name
                print(base_p)
                img_data["name"] = name
                project.save_annotations()
                
                img_data["img_info"] = img_i
                frame_data["selected_file"]["collection"] = collection_id
                
                frame_data["selected_file"]["name"] = base_p
                if frame_data["scale_changed"]:
                    frame_data["scale_changed"] = False
                    img_data["img_info"].change_scale(frame_data["img_scale"])
                    
                if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                    frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                    frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [img_data["img_info"].w, img_data["img_info"].h]

                frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [img_data["img_info"].scaled_w, img_data["img_info"].scaled_h]
        
            for i, img_info in enumerate(imgs):

                # img_info = project.imgs[k]
                name = img_info.name
                clicked, _ = imgui.selectable(
                            label=name + (" OK" if len(img_info.bboxes) > 0 else "") , selected=(frame_data["selected_file"]["idx"] == i and frame_data["selected_file"]["collection"] == collection_id)
                        )

                if clicked or frame_data["scale_changed"]:
                    
                    img_data["scale"] = frame_data["img_scale"]
                    if clicked:
                        frame_data["down_pressed"] = False

                        frame_data["scale_changed"] = True
                        base_p = name
                        img_data["name"] = name
                        project.save_annotations()
                        
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
