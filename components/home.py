import imgui
from components.data import Labels
from variables import frame_data
from .auto_annotation import header_auto_annotation, auto_ann_content
import glfw
from .projects import Project
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
            settings.settings_labels(project.labels)
            settings.settings_data_distribution()
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
    
    scale_changed, frame_data["img_scale"] = imgui.slider_float(
                label="Zoom",
                value=frame_data["img_scale"],
                min_value=0.5,
                max_value=2.0,
                format="%.1f",
            )
    if scale_changed:
        frame_data["scale_changed"] = True


def lab_content():
    global frame_data
    _files_list(frame_data, "annotate_preview")
    annotation._annotation_screen(frame_data, "annotate_preview")


def _files_list(frame_data, img_render_id):
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
