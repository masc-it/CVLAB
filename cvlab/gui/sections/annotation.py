
import math
from pathlib import Path
import subprocess
from threading import Thread

from cvlab.model.data import BBox, ImageInfo
from cvlab.model.app import App, FileList, Labeling
from cvlab.gui.base import Component
from threading import Thread
import imgui
import glfw
import numpy as np
from cvlab.yolov5 import detect
import os
from PIL import Image as PILImage
import sys
FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')

MIN_BBOX_SIZE = 5

class Annotator(Component):

    def __init__(self, app: App, ) -> None:
        super().__init__(app)

        self.x_offset = None
        self.scroll_right_margin = 60

        self.labeling = Labeling()

        self.auto_annotate = False

        self.image_data = app.image_data

        self.scroll_right_margin = 60
        
        self.img_render_id = "home"

        self.file_list_state = FileList()

        self.is_editing = False
        self.allow_edit = False
        self.interaction_bbox : BBox = None
        self.is_opening_file = False
        self.classifier = None
        
        t = Thread(target=self.__setup_pseudo_classifier)
        t.start()

    
    def __setup_pseudo_classifier(self):
        from cvlab.autoannotate_utils.unsupervised_classification import PseudoClassifier
        self.classifier = PseudoClassifier(
            Path("D:\\Documenti\\models\\ukb\\effnet2_tiny_128_simclr.onnx"),
            kb_path = Path("D:\\Documenti\\datasets\\ssl_ukb\\kb_letters\\"),
            features_size = 1024
        )

    def main(self):
        if self.x_offset is None:
            self.x_offset = int(self.app.viewport[0] / 5.5) + self.app.padding

        self.__options_menu()

        self.__files_list()
        self.__annotator()


    def __options_menu(self, ):

        """
            Main option menu.

            - Request a new Bounding box
            - Save annotations of current image
            - Request Auto Annotation
            - Zoom controls

        """

        annotate_click = imgui.button("New box" if not self.labeling.new_box_requested else "Cancel")        

        if annotate_click or imgui.is_key_pressed(glfw.KEY_N):
            self.labeling.new_box_requested = not self.labeling.new_box_requested

        imgui.same_line()
        save_click = imgui.button("Save")

        if save_click:

            self.project.save_annotations()

        imgui.same_line()

        autoannotate_click = imgui.button("Auto annotate" if not self.auto_annotate else "Draw box")
        if imgui.is_key_pressed(glfw.KEY_A):
            if self.labeling.new_box_requested == False:
                self.labeling.new_box_requested = (not self.labeling.new_box_requested)
            self.auto_annotate = (not self.auto_annotate)
        imgui.same_line()

        autoclassify_click = imgui.button("Add boxes to KB")
        if autoclassify_click:
           self.add_bboxes_to_kb()

        imgui.same_line()
        
        scale_changed, self.image_data.scale = imgui.slider_float(
                    label="Zoom",
                    value=self.image_data.scale,
                    min_value=0.5,
                    max_value=4.0,
                    format="%.1f",
                )
        if scale_changed:
            self.image_data.scale_changed = True
        
        if self.app.io.mouse_pos[0] > self.app.viewport[0] - self.scroll_right_margin:
            #frame_data["prev_cursor"] = glfw.ARROW_CURSOR
            glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(glfw.VRESIZE_CURSOR))
        else:
            glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(self.app.glfw["previous_cursor"]))

        mouse_wheel = self.app.io.mouse_wheel
        if self.app.is_dialog_open == False and mouse_wheel != 0 and self.app.io.mouse_pos[0] > self.x_offset and\
            self.app.io.mouse_pos[0] < self.app.viewport[0] - self.scroll_right_margin:
            self.image_data.scale += 0.2 if mouse_wheel > 0 else -0.2
            self.image_data.scale = min(4.0, self.image_data.scale)
            self.image_data.scale = max(0.5, self.image_data.scale)
            self.image_data.scale_changed = True
    
    def __files_list(self, ):
        
        """
            Shows the list of collections and images in the current project.

        """

        state = self.file_list_state
        w = self.x_offset - self.app.padding

        if self.file_list_state.is_open:
            imgui.begin_child(label="files_list", width=w, height=-1, border=False, )
            
            for collection_id in self.project.collections:

                collection_open = imgui.tree_node(self.project.collections[collection_id].name)
                if imgui.is_item_hovered():
                    dd_info, _ = self.project.get_data_distribution()
                    imgui.set_tooltip(f"Num. samples: {dd_info[self.project.collections[collection_id].name]['tot']}\nSplit Ratio: {dd_info[self.project.collections[collection_id].name]['ratio']:.2f}%")
                
                if collection_open:
                    state.open_collection_id = collection_id
                    imgs = self.project.get_images(collection_id)
                    
                    self.__options_controls(collection_id, imgs)
                        
                    imgui.tree_pop()

            imgui.end_child()
            imgui.same_line(position=self.x_offset)
        else:
            if state.open_collection_id is None:
                state.open_collection_id = list(self.project.collections.keys())[0]
            for collection_id in self.project.collections:
                imgs = self.project.get_images(collection_id)

                if collection_id == state.open_collection_id: 
                    self.__options_controls(collection_id, imgs)
                        
    
    def __options_controls(self, collection_id : str, imgs : "list[ImageInfo]"):
        
        state = self.file_list_state
        key_pressed = 0

        if imgui.is_key_pressed(glfw.KEY_DOWN):
            
            key_pressed = 1
        
        if imgui.is_key_pressed(glfw.KEY_UP):
            key_pressed = -1
        
        if key_pressed != 0:

            state.idx += key_pressed

            if state.idx == len(imgs) - 1:
                state.idx = 0
            elif state.idx < 0:
                state.idx = 0
            
            img_i = imgs[state.idx]

            name = img_i.name
            #img_data["scale"] = frame_data["img_scale"]

            self.image_data.scale_changed = True
            base_p = name
            print(base_p)

            self.image_data.name = name
            self.project.save_annotations()
            
            self.image_data.img_info = img_i
            state.collection_id = collection_id
            
            state.name = base_p
            if self.image_data.scale_changed:
                self.image_data.scale_changed = False
                self.image_data.img_info.change_scale(self.image_data.scale)
            
            self.image_data.has_changed = True

        for i, img_info in enumerate(imgs):

            # img_info = project.imgs[k]
            name = img_info.name

            if self.file_list_state.is_open:
                clicked, _ = imgui.selectable(
                            label=name + (" OK" if len(img_info.bboxes) > 0 else "") , selected=(state.idx == i and state.collection_id == collection_id)
                            
                        )
            else: 
                clicked = False

            if imgui.is_item_hovered() and imgui.is_key_pressed(glfw.KEY_F):
                self.explore(img_info.path)

            if clicked or self.image_data.scale_changed:
                
                if clicked:
                    self.app.btn_down_pressed = False

                    self.image_data.scale_changed = True
                    base_p = name
                    self.image_data.name = name
                    self.project.save_annotations()
                    
                    self.image_data.img_info = img_info
                    state.collection_id = collection_id
                    state.idx = i
                    state.name = base_p
                if self.image_data.scale_changed:
                    self.image_data.scale_changed = False
                    self.image_data.img_info.change_scale(self.image_data.scale)
                
                self.image_data.has_changed = True
    def __annotator(self):
        
        """
            Sub component that shows an image and its bounding boxes.

            - Handles bbox creation, editing, delete
            - Handles keyboard shortcuts
                - Request a new bbox (N)
                - Delete (BACKSPACE)
                - Edit bbox label (TAB)
                - Quick label switch (1-9)
                - Pseudo classify a hovered bbox (SPACE)


        """

        imgui.begin_child(label="img_preview", width=0, height=0, border=False, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR )
        
        padding = 8

        if self.image_data.texture is not None and self.image_data.img_info.scaled_w > imgui.get_content_region_available().x:
            padding = 22 # 8 + 14 = h_scrollbar height
        
        self.app.y_offset = self.app.viewport.y - imgui.get_content_region_available().y - padding # frame_data["y_offset_auto_ann"]
        if self.image_data.texture is not None:
            imgui.image(self.image_data.texture, self.image_data.img_info.scaled_w, self.image_data.img_info.scaled_h)
        

        draw_list : imgui._DrawList = imgui.get_window_draw_list()
        
        has_interacted = self.__handle_bbox_creation(draw_list)

        if not has_interacted and self.image_data.img_info is not None:

            self.__refresh_bboxes(draw_list)
        
            self.__handle_interaction()

            if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1) and self.app.is_dialog_open == False: # and frame_data["is_editing"] == False
                self.labeling.curr_bbox = None

        imgui.end_child()
    
    def __handle_bbox_creation(self, draw_list):

        """
            Handle bbox creation and editing.

            - Create a new bbox by dragging your mouse with left button.
            - Edit an existing bbox dragging your right mouse button.
        
        """
        if not self.app.is_dialog_open and self.image_data.texture is not None and (self.app.io.mouse_pos[0] <= self.x_offset or \
            self.app.io.mouse_pos[1] <= self.app.y_offset or self.app.io.mouse_pos[1] >= self.image_data.img_info.scaled_h + self.app.y_offset) :
                self.labeling.was_mouse_down = False
                self.labeling.new_box_requested = False
                self.labeling.curr_bbox = None
                return False
        # new bbox requested, was drawing a box and mouse is released => save bbox
        if self.labeling.curr_bbox is not None and self.app.is_dialog_open == False and self.labeling.was_mouse_down and self.labeling.new_box_requested and not imgui.is_mouse_down() :
            self.labeling.was_mouse_down = False
            #labeling["new_box_requested"] = False
            self.labeling.curr_bbox.width = abs(self.labeling.curr_bbox.xmax - self.labeling.curr_bbox.xmin)
            self.labeling.curr_bbox.height = abs(self.labeling.curr_bbox.ymax - self.labeling.curr_bbox.ymin)

            if self.auto_annotate:
                self.autoannotate(self.labeling.curr_bbox)
            else:
                self.image_data.img_info.bboxes.append(self.labeling.curr_bbox)
                self.image_data.img_info.set_changed(True)
            
                pseudo_label = self.auto_classify(self.labeling.curr_bbox)

                if pseudo_label != -1:
                    self.labeling.curr_bbox.label = pseudo_label
           
            self.labeling.curr_bbox = None
            if self.auto_annotate:
                self.auto_annotate = False
                self.labeling.curr_bbox = None
            
            return True
        # draw bbox following mouse coords
        elif not self.app.is_dialog_open and imgui.is_mouse_down() and self.labeling.new_box_requested:

            self.labeling.was_mouse_down = True
            curr_bbox : BBox = self.labeling.curr_bbox
            if curr_bbox is None:
                # save coords relative to the image, not app 
                curr_bbox = BBox(
                    self.app.io.mouse_pos[0] - self.x_offset + imgui.get_scroll_x(),
                    self.app.io.mouse_pos[1] - self.app.y_offset + imgui.get_scroll_y(),
                    0,
                    0,
                    self.labeling.selected_label
                )
                self.labeling.curr_bbox = curr_bbox
            
            curr_bbox.xmax = self.app.io.mouse_pos[0] - self.x_offset + imgui.get_scroll_x()
            curr_bbox.ymax = self.app.io.mouse_pos[1] - self.app.y_offset + imgui.get_scroll_y() 
            # convert image coords to screen coords

            # prevent to draw boxes right-2-left
            self.__check_bbox(curr_bbox)

            if curr_bbox.xmax - curr_bbox.xmin > MIN_BBOX_SIZE and\
                curr_bbox.ymax - curr_bbox.ymin > MIN_BBOX_SIZE : # bboxes must have at least 5px width/height
                draw_list.add_rect(
                    curr_bbox.xmin + self.x_offset - imgui.get_scroll_x(), 
                    curr_bbox.ymin +  self.app.y_offset - imgui.get_scroll_y() , 
                    curr_bbox.xmax + self.x_offset - imgui.get_scroll_x(), 
                    curr_bbox.ymax  +  self.app.y_offset - imgui.get_scroll_y(), 
                    imgui.get_color_u32_rgba(*self.project.labels.labels_map[curr_bbox.label].rgb, 255), 
                    thickness=1)
                self.image_data.img_info.set_changed(True)
            
            return True
        return False

    def __refresh_bboxes(self, draw_list):

        """
            Draw bboxes on screen where aach bbox has a rectangular label on top.

            - Handles bbox hovering

        """
        found = []
        
        for bbox in self.image_data.img_info.bboxes:
            
            # convert to app coordinates
            draw_list.add_rect(
                bbox.xmin + self.x_offset - imgui.get_scroll_x(), 
                bbox.ymin + self.app.y_offset - imgui.get_scroll_y(), 
                bbox.xmax + self.x_offset - imgui.get_scroll_x(), 
                bbox.ymax + self.app.y_offset - imgui.get_scroll_y() , 
                imgui.get_color_u32_rgba(*self.project.labels.labels_map[bbox.label].rgb, 255),
                thickness=1
            )

            # draw rectangle on top of bbox
            draw_list.add_rect_filled(
                bbox.xmin + self.x_offset - imgui.get_scroll_x(), 
                bbox.ymin - 12 + self.app.y_offset - imgui.get_scroll_y(), 
                bbox.xmax + self.x_offset - imgui.get_scroll_x(), 
                bbox.ymin + self.app.y_offset - imgui.get_scroll_y(), 
                imgui.get_color_u32_rgba(*self.project.labels.labels_map[bbox.label].rgb, 255)
            )

            imgui.set_cursor_screen_pos(
                (bbox.xmin + self.x_offset - imgui.get_scroll_x(),
                bbox.ymin - 14 - imgui.get_scroll_y() + self.app.y_offset
                )
            )
            imgui.text(
                self.project.labels.labels_map[bbox.label].label[:3]
            )

            # handle bbox hovering
            if not self.app.is_dialog_open and imgui.get_mouse_pos()[0] >= bbox.xmin + self.x_offset - imgui.get_scroll_x() and\
                imgui.get_mouse_pos()[0] <= bbox.xmax + self.x_offset - imgui.get_scroll_x() and\
                imgui.get_mouse_pos()[1] >= bbox.ymin - imgui.get_scroll_y() +  self.app.y_offset  and\
                imgui.get_mouse_pos()[1] <=  bbox.ymax - imgui.get_scroll_y() +  self.app.y_offset :
                
                if self.app.glfw["previous_cursor"] != glfw.HAND_CURSOR:
                    glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(glfw.HAND_CURSOR))
                    self.app.glfw["previous_cursor"] = glfw.HAND_CURSOR
                    #print("created")
                found.append(bbox)
        
        if self.app.is_dialog_open:
            return
        # take the closest window. Needed for nested bboxes.
        ordered_found = sorted(found, key=lambda x: abs(imgui.get_mouse_pos()[0] - x.xmin))

        # get bbox hovered by mouse 
        if len(ordered_found) > 0 and self.labeling.curr_bbox is None:
            self.labeling.curr_bbox = ordered_found[0]
        if self.app.glfw["previous_cursor"] != glfw.ARROW_CURSOR and found == [] and not imgui.is_mouse_down(1):
            self.app.glfw["previous_cursor"] = glfw.ARROW_CURSOR
            glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(glfw.ARROW_CURSOR))
    
    def __handle_interaction(self,):
        """
            - Handle bbox dragging (Left mouse button)
            - Handle bbox resize   (Right mouse button)
            - Keyboard shortcuts
        """
        if not self.app.is_dialog_open: # self.allow_edit and 
            self.__handle_bbox_drag()
            self.__handle_bbox_resize()

            self.__handle_shortcuts()
        self.__dialog_label_selection(self.labeling.curr_bbox)
            
    def __handle_bbox_drag(self):

        if self.labeling.curr_bbox is not None and self.image_data.img_info is not None and\
            self.app.io.mouse_pos[0] < self.app.viewport[0] - self.scroll_right_margin and imgui.is_mouse_down():

            mouse_pos_x = self.app.io.mouse_pos[0]
            mouse_pos_y = self.app.io.mouse_pos[1]

            # save bbox-relative mouse offset to avoid snapping when moving 
            if self.interaction_bbox is None:
                self.interaction_bbox = self.labeling.curr_bbox

                self.labeling.x_offset = self.labeling.curr_bbox.width - ( self.labeling.curr_bbox.xmax + self.x_offset - imgui.get_scroll_x() - mouse_pos_x  )  
                self.labeling.y_offset = self.labeling.curr_bbox.height - (self.labeling.curr_bbox.ymax - mouse_pos_y + self.app.y_offset - imgui.get_scroll_y()) 
    
            mouse_pos_x -= self.labeling.x_offset
            mouse_pos_y -= self.labeling.y_offset

            new_xmin = mouse_pos_x - self.x_offset + imgui.get_scroll_x()
            if new_xmin >= 0 and new_xmin + self.labeling.curr_bbox.width < self.image_data.img_info.scaled_w:
                self.labeling.curr_bbox.xmin = max(0, new_xmin)
            
            new_xmax = self.labeling.curr_bbox.xmin + self.labeling.curr_bbox.width
            if new_xmax <= self.image_data.img_info.scaled_w:
                self.labeling.curr_bbox.xmax = min(self.image_data.img_info.scaled_w, new_xmax)

            new_ymin = mouse_pos_y - self.app.y_offset + imgui.get_scroll_y() 

            if new_ymin >= 0 and new_ymin + self.labeling.curr_bbox.height < self.image_data.img_info.scaled_h:        
                self.labeling.curr_bbox.ymin = max(0, new_ymin)  #frame_data["io"].mouse_pos[1] + imgui.get_scroll_y() - frame_data["y_offset"] - labeling["curr_bbox"]["height"]/2 # -(labeling["curr_bbox"]["y_max"] - frame_data["io"].mouse_pos[1] )  #
            
            self.labeling.curr_bbox.ymax = min(self.image_data.img_info.scaled_h, self.labeling.curr_bbox.ymin + self.labeling.curr_bbox.height)
        
            self.image_data.img_info.set_changed(True)
        else:
            self.interaction_bbox = None
    
    def __handle_bbox_resize(self):
       
        if imgui.is_mouse_down(1) and self.labeling.curr_bbox is not None:

            self.labeling.curr_bbox.xmax = self.app.io.mouse_pos[0] - self.x_offset + imgui.get_scroll_x()
            self.labeling.curr_bbox.ymax = self.app.io.mouse_pos[1] - self.app.y_offset + imgui.get_scroll_y()
            
            # prevent to draw boxes right-2-left
            self.__check_bbox(self.labeling.curr_bbox)
            
            self.labeling.curr_bbox.width = abs(self.labeling.curr_bbox.xmax - self.labeling.curr_bbox.xmin) 
            self.labeling.curr_bbox.height = abs(self.labeling.curr_bbox.ymax - self.labeling.curr_bbox.ymin)

            self.image_data.img_info.set_changed(True)
    
    def __handle_shortcuts(self):

        # print(self.app.io.mouse_pos)
        if imgui.is_key_pressed(glfw.KEY_LEFT_CONTROL):
            self.file_list_state.is_open = not self.file_list_state.is_open

            if self.file_list_state.is_open:
                self.app.padding = 20 # 8 + 12
                self.x_offset = int(self.app.viewport[0] / 5.5) + self.app.padding
            else:
                self.app.padding = 8
                self.x_offset = self.app.padding  # int(self.app.viewport[0] / 5.5) + self.app.padding 
            #print(self.x_offset)

        # delete bbox on BACKSPACE PRESS
        if imgui.is_key_pressed(glfw.KEY_BACKSPACE) and self.labeling.curr_bbox is not None:
            self.image_data.img_info.bboxes.remove(self.labeling.curr_bbox)
            self.labeling.curr_bbox = None
            self.image_data.img_info.set_changed(True)
                
        """ for i in self.project.labels.shortcuts:
            if i == "":
                continue
            if imgui.is_key_pressed(int(i)+glfw.KEY_0) : 
                self.labeling.selected_label = self.project.labels.shortcuts[i].index
                if self.labeling.curr_bbox is not None:
                    self.labeling.curr_bbox.label = self.project.labels.shortcuts[i].index
                    self.image_data.img_info.set_changed(True)
                break """
        
        if self.labeling.curr_bbox is not None:
            l = self.project.labels.labels_map[self.labeling.curr_bbox.label].label
            imgui.set_tooltip(f"Label: {l}")

        # edit label dialog
        if imgui.is_key_pressed(glfw.KEY_TAB) and self.labeling.curr_bbox is not None:
            
            imgui.open_popup("Label")
            imgui.set_next_window_size(350, 600)
            
            self.app.is_dialog_open = True
            
        # duplicate bbox
        if imgui.is_key_pressed(glfw.KEY_D) and self.labeling.curr_bbox is not None:
            
            self.labeling.new_box_requested = False

            xmin = self.labeling.curr_bbox.xmax + 3
            xmax = xmin + self.labeling.curr_bbox.width

            bbox_copy = BBox(
                xmin,
                self.labeling.curr_bbox.ymin,
                xmax,
                self.labeling.curr_bbox.ymax,
                self.labeling.curr_bbox.label
            )
            self.image_data.img_info.bboxes.append(bbox_copy)
        
        if imgui.is_key_pressed(glfw.KEY_SPACE) and self.labeling.curr_bbox is not None:

            auto_classify_label = self.auto_classify(self.labeling.curr_bbox)
            if auto_classify_label != -1:
                self.labeling.curr_bbox.label = auto_classify_label
                self.auto_classify_label = -1

    def __check_bbox(self, bbox : BBox ):
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

        bbox.xmax = min(self.image_data.img_info.scaled_w, bbox.xmax)
        bbox.ymax = min(self.image_data.img_info.scaled_h, bbox.ymax)

        if bbox.xmax - bbox.xmin <= MIN_BBOX_SIZE:
            bbox.xmax = bbox.xmin + MIN_BBOX_SIZE
        if bbox.ymax - bbox.ymin <= MIN_BBOX_SIZE:
            bbox.ymax = bbox.ymin + MIN_BBOX_SIZE
        bbox.update_size()
    
    def __dialog_label_selection(self, bbox: BBox):
        """
            Dialog to manually select/edit a bbox label.
        """
        if imgui.begin_popup_modal("Label", flags=imgui.WINDOW_NO_RESIZE )[0]: # imgui.WINDOW_NO_RESIZE
            
            self.app.is_dialog_open = True
            imgui.begin_child(label="labels_listt", width=300, height=500, border=False, )

            for label in self.project.labels:

                clicked, _ = imgui.selectable(
                    label=label.label , selected=(bbox.label == label.index)
                )
                if clicked:
                    bbox.label = label.index
                    self.image_data.img_info.set_changed(True)
                    self.app.is_dialog_open = False
                    imgui.close_current_popup()
            imgui.end_child()
            imgui.end_popup()
    
    # AUTO ANNOTATION / CLASSIFICATION

    def add_bboxes_to_kb(self):

        img_info_path = Path(self.image_data.img_info.path)

        img = PILImage.open(img_info_path).convert("RGB")

        for i, bbox in enumerate(self.image_data.img_info.bboxes):
            random_name = f"{img_info_path.stem}_{i}"
            crop_path = (self.classifier.kb_path / "imgs" / random_name ).with_suffix(".jpg")

            if crop_path.exists():
                continue
            scaled_bbox = bbox.scale((self.image_data.img_info.w, self.image_data.img_info.h), (self.image_data.img_info.orig_w, self.image_data.img_info.orig_h))
            crop = img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax)))
            
            crop.save(crop_path)

            self.classifier.add_img_to_kb( img_info_path, crop_path, bbox.label)

        self.classifier.save_kb_single(img_info_path.stem)
        print("kb saved")

    def auto_classify(self, bbox: BBox):

        img = PILImage.open(self.image_data.img_info.path).convert("RGB")
        scaled_bbox = bbox.scale((self.image_data.img_info.w, self.image_data.img_info.h), (self.image_data.img_info.orig_w, self.image_data.img_info.orig_h))
        crop = img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax)))

        label, _, _ = self.classifier.predict_label(img_path=crop)
        if label is not None:
            return label
            #print(frame_data["project"].labels.labels_map[str(label)].label)
        else:
            return -1

    @staticmethod
    def get_iou(bbox1:BBox, bbox2: BBox):
            """
            Calculate the Intersection over Union (IoU) of two bounding boxes.

            Returns
            -------
            float
                in [0, 1]
            """

            # determine the coordinates of the intersection rectangle
            x_left = max(bbox1.xmin, bbox2.xmin)
            y_top = max(bbox1.ymin, bbox2.ymin)
            x_right = min(bbox1.xmax, bbox2.xmax)
            y_bottom = min(bbox1.ymax, bbox2.ymax)

            if x_right < x_left or y_bottom < y_top:
                return 0.0

            # The intersection of two axis-aligned bounding boxes is always an
            # axis-aligned bounding box
            intersection_area = (x_right - x_left) * (y_bottom - y_top)

            # compute the area of both AABBs
            bb1_area = (bbox1.xmax - bbox1.xmin) * (bbox1.ymax - bbox1.ymin)
            bb2_area = (bbox2.xmax - bbox2.xmin) * (bbox2.ymax - bbox2.ymin)

            # compute the intersection over union by taking the intersection
            # area and dividing it by the sum of prediction + ground-truth
            # areas - the interesection area
            iou = intersection_area / float(bb1_area + bb2_area - intersection_area)

            return iou
    
    def start_autoann(self, img_path: Path):
        
        predictions = detect.run(weights="D:/Download/letters_best0507b.pt", imgsz=[1920, 1080], conf_thres=0.2, iou_thres=0.5, save_conf=True,
                    exist_ok=True, save_txt=False, source=img_path, project=None, name=None,)

        for _, (bboxes, img)  in enumerate(predictions):
            
            #print(bboxes)
            # exp.imgs.append(img_info)
            for bbox in bboxes:
                bbox : BBox = BBox(bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"], bbox["class"], bbox["conf"])

                if self.image_data.img_info.scale != 1:
                    bbox = bbox.scale((self.image_data.img_info.orig_w, self.image_data.img_info.orig_h), (self.image_data.img_info.scaled_w, self.image_data.img_info.scaled_h))

                same = list(filter(lambda x: x.xmin == bbox.xmin and x.ymin == bbox.ymin or ( bbox.xmin > x.xmin and bbox.ymin > x.ymin and bbox.xmax < x.xmax and bbox.ymax < x.ymax ) or ( bbox.xmin < x.xmin and bbox.ymin < x.ymin and bbox.xmax > x.xmax and bbox.ymax > x.ymax ) or self.get_iou(bbox, x) > 0.6, self.image_data.img_info.bboxes))
                if len(same) == 0:
                    self.image_data.img_info.add_bbox(bbox)
                else:
                    same.append(bbox)
                    same = list(sorted(same, key= lambda x: x.conf, reverse=True))

                    for d in same[1:]:
                        self.image_data.img_info.bboxes.remove(d)
                    
                    self.image_data.img_info.bboxes.append(same[0])


    def autoannotate(self, bbox: BBox):
        # load image
        img = PILImage.open(self.image_data.img_info.path).convert("RGB")

        # mask area outside selected bbox
        arr = np.zeros((img.size[1], img.size[0], 3))
        scaled_bbox = bbox.scale((self.image_data.img_info.w, self.image_data.img_info.h), (self.image_data.img_info.orig_w, self.image_data.img_info.orig_h))
        crop = np.array(img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax))))
        arr[math.ceil(scaled_bbox.ymin):math.ceil(scaled_bbox.ymax), math.ceil(scaled_bbox.xmin):math.ceil(scaled_bbox.xmax), ...] = crop
        
        img = PILImage.fromarray(np.uint8(arr))
        img.save("lmao.jpg")
        # run predictions

        t = Thread(target=(self.start_autoann), args=(Path("lmao.jpg"), ))
        t.start()
    
    def explore(self, path):
        
        if sys.platform == "win32":
            # explorer would choke on forward slashes
            path = os.path.normpath(path)

            if os.path.isdir(path):
                subprocess.run([FILEBROWSER_PATH, path])
            elif os.path.isfile(path):
                subprocess.run([FILEBROWSER_PATH, '/select,', path])
        elif sys.platform == 'linux2':
            subprocess.run(["xdg-open", path])
        elif sys.platform == 'darwin':
            subprocess.call(["open", "-R", path])