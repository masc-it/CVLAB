from pathlib import Path
from autoannotate_utils.unsupervised_classification import PseudoClassifier

frame_data = {

    "num_imgs" : 0,
    "is_running": False,
    "img": "",
    "image_texture" : None,
    "done": False,
    "predictions" : None,
    "imgs" : None,
    "selected_file" : {
        "path": None,
        "idx": 0,
        "texture":None,
        "name": "",
        "collection": "",
        "image_width" : None,
        "image_height": None
    },
    "labeling": {
        "selected_label": "0",
        "new_box_requested": False,
        "curr_bbox": None,
        
        "was_mouse_down": False,
        "was_dragging": False,
        "x_offset": 0,
        "y_offset": 0
    },
    "fonts": {
        
    },
    "classifier": 
        PseudoClassifier(
            Path("D:\\Documenti\\models\\ukb\\effnet2_tiny_128_simclr.onnx"),
            kb_path = Path("D:\\Documenti\\datasets\\ssl_ukb\\kb_letters\\"),
            features_size = 1024
        ),
    "down_pressed": False,
    "can_resize": False,
    "autoclassifier": -1,
    "autoannotate": False,
    "is_editing": False,
    "export_running": False,
    "export_collection": None,
    "export_progress": 0,
    "export_counts": {},
    "export_click": False,
    "export_table": {},
    "imgs_to_render": {},
    "imgs_info" : {},
    "img_scale": 1.0,
    "scale_changed": False,
    "is_dialog_open": False,
    "prev_cursor": 221185, # glfw.ARROW_CURSOR
    "y_offset": 88,
    "y_offset_lab": 88,
    "y_offset_auto_ann": 117,
    "progress": 0,
    "folder_path": "D:/Projects/python/semantics/project/test_final/imgs", #D:/Projects/python/semantics/project/test_final/images
    "model_path": "D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt", #D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt
    "threshold_conf": 0.55,
    "threshold_iou" : 0.45
}