from cvlab.components.data import BBox, CollectionInfo, ImageInfo
import imgui

from cvlab.components.projects import Project

class Labeling(object):

    def __init__(self,) -> None:
        self.selected_label = "0"

        self.curr_bbox : BBox = None
        self.x_offset = 0
        self.y_offset = 0

        # Labeling events
        self.new_box_requested = False
        self.was_mouse_down = False
        self.was_dragging = False

"""
"prev_name": "",
            "name": "",
            "texture": None,
            "scale": 1.0,
            "img_info" : None
"""
class Image(object):

    def __init__(self) -> None:
        
        self.prev_name = ""
        self.name = ""
        self.texture = None
        
        self.img_info : ImageInfo = None

        self.scale_changed = False
        self.scale = 1.0


"""
"selected_file" : {
        "path": None,
        "idx": 0,
        "texture":None,
        "name": "",
        "collection": "",
        "image_width" : None,
        "image_height": None
    },
"""
class FileList(object):

    def __init__(self) -> None:
        self.path : str = None
        self.idx : int = 0
        self.texture = None
        self.name : str = None
        self.collection_id : str = None
        self.image_width : int = None
        self.image_height : int = None

class App(object):
    """
        Main class containing the whole application state.

    """

    def __init__(self) -> None:

        # imgui useful props
        self.io = None #imgui.get_io()
        self.viewport = None #imgui.get_main_viewport().size
        self.glfw = {}

        self.fonts = {}
        
        # OFFSETS   
        self.y_offset = 88
        self.y_offset_lab = 88

        self.padding = 20

        # Loaded project
        self.project : Project = None

        self.is_dialog_open = False

        self.auto_annotate = False

        self.btn_down_pressed = False
        # ------ HOME -------------
        
        self.export_dialog_click = False
        




    
