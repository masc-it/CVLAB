from pathlib import Path
from ..model.data import *
import imgui
from ..model.project import Project
from yolov5 import detect
import  os
import threading
from . import annotation
from .file_selector import file_selector
from cvlab.gui.custom_utils import save_img_annotations


def start_inference(frame_data, exp: Experiment):
    
    predictions = detect.run(weights=exp.model_path, imgsz=[1280, 1280], conf_thres=exp.threshold_conf, iou_thres=exp.threshold_iou, save_conf=True,
                exist_ok=True, save_txt=True, source=exp.data_path, project=exp.data_path + "/exp", name="predictions",)
    
    frame_data["imgs_to_render"]["inference_preview"]["scale"] = 1

    for _, (bboxes, img)  in enumerate(predictions):
        
        frame_data["imgs_to_render"]["inference_preview"]["name"] = img
        name_ext = os.path.basename(img).rsplit('.')
        img_info = ImageInfo(name_ext[0], name_ext[1], CollectionInfo(exp.exp_name, exp.exp_name, exp.data_path ))
        
        # exp.imgs.append(img_info)
        for bbox in bboxes:
            bbox : BBox = BBox(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"], bbox["class"], bbox["conf"])
            img_info.add_bbox(bbox)
        frame_data["imgs_to_render"]["inference_preview"]["img_info"] = img_info
        
        exp.add_image(img_info)
        save_img_annotations(img_info)
        # print(img)

        # frame_data["img"] = img
        exp.progress += 0.1
        if not exp.is_running:
            
            break
    
    frame_data["imgs_to_render"]["inference_preview"]["img_info"] = None
    frame_data["imgs_to_render"]["inference_preview"]["texture"] = None
    exp.is_running = False
    exp.progress = 0
    frame_data["done"] = True
    frame_data["is_running"] = False
    


def auto_ann_content(frame_data):
    _files_list(frame_data, "inference_preview")

    if frame_data["is_running"]:
        imgui.begin_child("i_progress")
        imgui.progress_bar(
            fraction=frame_data['experiment'].progress * 10 / frame_data["num_imgs"] , 
            size=(-1, 0.0),
            overlay=f"{int(frame_data['experiment'].progress * 10)}/{frame_data['num_imgs']}"
        )
        annotation._annotation_screen(frame_data, "inference_preview", allow_edit=False)
        imgui.end_child()
    else:
        annotation._annotation_screen(frame_data, "inference_preview", allow_edit=False)


def header_auto_annotation(frame_data):

    project : Project = frame_data["project"]
    
    """ if frame_data["is_running"]:
        imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha *  0.5) """
    
    if imgui.button("New session"):
        imgui.open_popup("Auto-annotation session")
        imgui.set_next_window_size(700, 350)
        frame_data["is_dialog_open"] = True
        frame_data["experiment"] = Experiment("D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt", "D:\\Projects\\python\\semantics\\project\\test_final\\imgs_exp2", "")

    if imgui.begin_popup_modal("Auto-annotation session", flags=imgui.WINDOW_NO_RESIZE )[0]:
        
        imgui.begin_child(label="auto_ann_content", height=250, border=False, )
        imgui.columns(1, "header_2", False)

        model_btn_title = "Choose model path..."
        if imgui.button(model_btn_title):
            imgui.open_popup("Choose model path...")

        model_file = file_selector("Choose model path...", False)
        if model_file is not None:
            frame_data["experiment"].model_path = model_file
        
        if frame_data["experiment"].model_path != "":
            imgui.same_line()
            imgui.text(frame_data["experiment"].model_path)
        
        images_btn_title = "Choose images directory..."
        if imgui.button(images_btn_title):
            imgui.open_popup(images_btn_title)
        images_path = file_selector(images_btn_title, True)
        if images_path is not None:
            frame_data["experiment"].data_path = images_path
 
        if frame_data["experiment"].data_path != "":
            imgui.same_line()
            imgui.text(frame_data["experiment"].data_path)
        
        _, frame_data["experiment"].exp_name = imgui.input_text("Name",frame_data["experiment"].exp_name, 128)
        imgui.separator()
        imgui.push_item_width(520)
        _, frame_data["experiment"].threshold_conf = imgui.slider_float(
                    label="Confidence threshold",
                    value=frame_data["experiment"].threshold_conf,
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                )
        
        _, frame_data["experiment"].threshold_iou = imgui.slider_float(
                    label="IoU threshold",
                    value=frame_data["experiment"].threshold_iou,
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                )
                
        imgui.pop_item_width()
        imgui.separator()

        imgui.end_child()
        if imgui.button("Start annotation"):

            frame_data["experiment"].update_info()
            frame_data["experiment"].is_running = True
            frame_data["is_running"] = True
            frame_data["experiment"].progress = 0
            frame_data["done"] = False

            frame_data["num_imgs"] = frame_data["experiment"].num_imgs
            frame_data["project"].save_experiment(frame_data["experiment"])
            thread = threading.Thread(target=start_inference, args=(frame_data, frame_data["experiment"]))
            thread.start()
            imgui.close_current_popup()
            frame_data["is_dialog_open"] = False
        imgui.same_line()
        if imgui.button("Close"):
            imgui.close_current_popup()
            frame_data["is_dialog_open"] = False
        
        imgui.end_popup()
    
    """ if frame_data["is_running"]:
        imgui.internal.pop_item_flag()
        imgui.pop_style_var() """

    imgui.columns(1)

    if frame_data["is_running"]:
        start_clicked = imgui.button("Stop analysis")
    
        if start_clicked:

            if frame_data["is_running"]:
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

def inference_progress(frame_data):

    img_data = frame_data["imgs_to_render"]["inference_preview"]
    if frame_data["is_running"]:
        
        imgui.columns(3,"progr", False)
        imgui.next_column()
        imgui.progress_bar(
            fraction=frame_data['experiment'].progress * 10 / frame_data["num_imgs"] , 
            size=(-1, 0.0),
            overlay=f"{int(frame_data['experiment'].progress * 10)}/{frame_data['num_imgs']}"
        )
        imgui.columns(1)
        imgui.spacing()
        if img_data["texture"] is not None:
            imgui.same_line((frame_data["viewport"][0] / 2) - (img_data["width"] / 2))
            imgui.image(img_data["texture"], img_data["width"], img_data["height"])
