from .data import *
import imgui
from .projects import Project
from yolov5 import detect
import glob, os
import threading
from . import annotation
from .file_selector import file_selector


def start_inference(frame_data):
    
    predictions = detect.run(weights=frame_data["model_path"], imgsz=[1280, 1280], conf_thres=frame_data["threshold_conf"], iou_thres=frame_data["threshold_iou"], save_conf=True,
                exist_ok=True, save_txt=True, source=frame_data["folder_path"], project=frame_data["folder_path"] + "/exp", name="predictions",)
    
    frame_data["imgs_to_render"]["inference_preview"]["scale"] = 1

    exp : Experiment = frame_data["experiment"]

    coll_info : CollectionInfo = CollectionInfo(exp.exp_name, exp.exp_name, exp.data_path)

    for _, (bbox, img)  in enumerate(predictions):

        bbox : BBox = BBox(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"], bbox["class"], bbox["conf"])
        name_ext = os.path.basename(img).rsplit('.')
        img_info = ImageInfo(name_ext[0], name_ext[1], coll_info)
        img_info.add_bbox(bbox)
        # print(img)
        frame_data["imgs_to_render"]["inference_preview"]["name"] = img
        # frame_data["img"] = img
        frame_data["progress"] += 0.1
        if not frame_data["is_running"]:
            break
        
    frame_data["is_running"] = False
    frame_data["progress"] = 0
    frame_data["done"] = True

def auto_ann_content(frame_data):
    _files_list(frame_data, "inference_preview")
    annotation._annotation_screen(frame_data, "inference_preview", allow_edit=False)


def header_auto_annotation(frame_data):

    project : Project = frame_data["project"]
    
    if frame_data["is_running"]:
        imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha *  0.5)
    
    if imgui.button("New session"):
        imgui.open_popup("Auto-annotation session")
        imgui.set_next_window_size(700, 350)
    if imgui.begin_popup_modal("Auto-annotation session", flags=imgui.WINDOW_NO_RESIZE )[0]:
        
        imgui.begin_child(label="auto_ann_content", height=250, border=False, )
        imgui.columns(1, "header_2", False)

        model_btn_title = "Choose model path..."
        if imgui.button(model_btn_title):
            imgui.open_popup("Choose model path...")

        model_file = file_selector("Choose model path...", False)
        if model_file is not None:
            project.model_path = model_file
        
        
        if project.model_path != "":
            imgui.same_line()
            imgui.text(project.model_path)
        
        images_btn_title = "Choose images directory..."
        if imgui.button(images_btn_title):
            imgui.open_popup(images_btn_title)
        images_path = file_selector(images_btn_title, True)
        if images_path is not None:
            frame_data["folder_path"] = images_path
 
        if frame_data["folder_path"] != "":
            imgui.same_line()
            imgui.text(frame_data["folder_path"])
        
        imgui.separator()
        imgui.push_item_width(520)
        _, frame_data["threshold_conf"] = imgui.slider_float(
                    label="Confidence threshold",
                    value=frame_data["threshold_conf"],
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                )
        
        _, frame_data["threshold_iou"] = imgui.slider_float(
                    label="IoU threshold",
                    value=frame_data["threshold_iou"],
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                )
        imgui.pop_item_width()
        imgui.separator()

        imgui.end_child()
        if imgui.button("Start annotation"):
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button("Close"):
            imgui.close_current_popup()
        
        imgui.end_popup()
    
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

def _files_list(frame_data, img_render_id):
    project : Project = frame_data["project"]
    experiments : dict[str, Experiment] = project.experiments

    img_data = frame_data["imgs_to_render"][img_render_id]
    
    # add 20 more (scrollbar)
    frame_data["x_offset"] = int(frame_data["viewport"][0] / 5) + 20

    imgui.begin_child(label="files_list", width=frame_data["x_offset"] - 20, height=-1, border=False, )
    
    for exp_id in experiments:
        exp = experiments[exp_id]
        if imgui.tree_node(exp.exp_name):
            for i, img_info in enumerate(exp.imgs):

                # img_info = project.imgs[k]
                name = img_info.name
                clicked, _ = imgui.selectable(
                            label=name, selected=(frame_data["selected_file"]["idx"] == i and frame_data["selected_file"]["collection"] == exp_id)
                        )
                
                if clicked or frame_data["scale_changed"]:
                    
                    img_data["scale"] = frame_data["img_scale"]
                    if clicked:
                        frame_data["scale_changed"] = True
                        base_p = name
                        img_data["name"] = name
                        
                        img_data["img_info"] = img_info
                        frame_data["selected_file"]["collection"] = exp_id
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
