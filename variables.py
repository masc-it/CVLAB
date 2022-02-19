
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
        
        "was_mouse_down": False,
        "was_dragging": False,
        "x_offset": 0,
        "y_offset": 0
    },
    
    "imgs_to_render": {},
    "imgs_info" : {},
    "prev_cursor": 221185, # glfw.ARROW_CURSOR
    "y_offset": 146,
    "progress": 0,
    "folder_path": "D:/Projects/python/semantics/project/test_final/imgs", #D:/Projects/python/semantics/project/test_final/images
    "model_path": "D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt", #D:/Projects/python/pdf-toolbox/pdf_toolbox/backend/data/pdf_best_multi_nano.pt
    "threshold_conf": 0.55,
    "threshold_iou" : 0.45
}