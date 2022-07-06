from cvlab.model.data import BBox, ImageInfo

from cvlab.model.project import Project
import pygame
import OpenGL.GL as gl

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

class Image(object):

    def __init__(self) -> None:
        
        self.prev_name = ""
        self.name = ""
        self.texture = None
        
        self.img_info : ImageInfo = None

        self.scale_changed = False
        self.scale = 1.0

        self.has_changed = False


class FileList(object):

    def __init__(self) -> None:
        self.path : str = None
        self.idx : int = 0
        self.texture = None
        self.name : str = None
        self.collection_id : str = None
        self.image_width : int = None
        self.image_height : int = None

        self.is_open = True

        self.open_collection_id = None

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
        self.classifier = None
        self.btn_down_pressed = False

        self.settings_changed = False
        # ------ ANNOTATOR -------------

        self.image_data = Image()
        
        self.export_dialog_click = False
        

    def load_image_from_file(self, image_name, scale=1):
        image = pygame.image.load(image_name)

        textureSurface = pygame.transform.flip(image, False, True)
        
        orig_width = textureSurface.get_width()
        orig_height = textureSurface.get_height()

        """ print("orig")
        print(orig_width)
        print(orig_height) """

        #print(f"orig ar: {orig_width/orig_height}")

        if scale != 1:
            """ w = orig_width * scale
            w = w * (orig_height/orig_width)
            h = orig_height """
            """ basewidth = int(orig_width * scale)
            wpercent = (basewidth/float(orig_width))
            hsize = int((float(orig_height)*float(wpercent))) """
            scaled_w = int(orig_width*scale)
            scaled_h = int(orig_height*scale)
            textureSurface = pygame.transform.smoothscale(textureSurface, [scaled_w, scaled_h] )
        textureData = pygame.image.tostring(textureSurface, "RGB", 1)

        width = textureSurface.get_width()
        height = textureSurface.get_height()

        """ print("scaled")
        print(width)
        print(height) """
        # print(f"scaled ar: {width/height}")
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB,
                        gl.GL_UNSIGNED_BYTE, textureData)

        return {
            "texture": texture, 
            "scaled_width": width, 
            "scaled_height": height, 
            "orig_width": orig_width,
            "orig_height": orig_height
        }

    def _load_image_texture(self, image_data : Image):
        
        img_data = self.load_image_from_file(image_data.img_info.path, image_data.scale)  
        
        image_data.texture = img_data["texture"]


    def load_images(self, ):

        image_data = self.image_data

        if image_data.img_info is not None and image_data.has_changed:
            image_data.has_changed = False
            
            self._load_image_texture(image_data)


    
