
from cvlab.gui.app import App, FileList, Image, Labeling
from cvlab.gui.base import Component

import imgui
import glfw

class Home(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)

        self.x_offset = int(self.viewport[0] / 5) + self.app.padding

        self.scroll_right_margin = 60

        self.labeling = Labeling()

        self.auto_annotate = False

        self.image_data = Image()

        self.scroll_right_margin = 60
        
        self.img_render_id = "home"

        self.file_list_state = FileList()

    
    def main(self):
        
        self.__header()
        self.__files_list()

    def __header(self, ):
    
        if imgui.begin_tab_bar("sections"):

            if imgui.begin_tab_item("LAB")[0]:

                self.header_lab()
                #lab_content()
                imgui.end_tab_item()
            
            if imgui.begin_tab_item("Auto annotation")[0]:
                #print(imgui.get_mouse_pos())
                #frame_data["y_offset"] = imgui.get_main_viewport().size.y - imgui.get_content_region_available().y - 8 # frame_data["y_offset_auto_ann"]
                
                #header_auto_annotation(frame_data)
                #auto_ann_content(frame_data)
                
                imgui.end_tab_item()
            
            if imgui.begin_tab_item("Settings & Info")[0]:

                project = self.project
                imgui.begin_child(label="setting_section", border=False, )
                #settings.settings_labels(project.labels)
                #settings.settings_dd()
                #settings.settings_label_distribution()
                imgui.end_child()
                imgui.end_tab_item()
            imgui.end_tab_bar()


    def header_lab(self, ):
        
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
            #annotation.add_bboxes_to_kb(frame_data, self.img_info)
            pass

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
        
        if self.io.mouse_pos[0] > self.viewport[0] - self.scroll_right_margin:
            #frame_data["prev_cursor"] = glfw.ARROW_CURSOR
            glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(glfw.VRESIZE_CURSOR))
        else:
            glfw.set_cursor(self.app.glfw["window"], glfw.create_standard_cursor(self.app.glfw["previous_cursor"]))

        mouse_wheel = self.io.mouse_wheel
        if self.app.is_dialog_open == False and mouse_wheel != 0 and self.io.mouse_pos[0] > self.x_offset and\
            self.io.mouse_pos[0] < self.viewport[0] - self.scroll_right_margin:
            self.image_data.scale += 0.2 if mouse_wheel > 0 else -0.2
            self.image_data.scale = min(4.0, self.image_data.scale)
            self.image_data.scale = max(0.5, self.image_data.scale)
            self.image_data.scale_changed = True
        
    def lab_content(self, ):

        self.__files_list()
        #annotation._annotation_screen(frame_data, "annotate_preview")


    def __files_list(self, ):
        
        state = self.file_list_state
        w = self.x_offset - self.app.padding
        imgui.begin_child(label="files_list", width=w, height=-1, border=False, )
        
        for collection_id in self.project.collections:

            collection_open = imgui.tree_node(self.project.collections[collection_id].name)
            if imgui.is_item_hovered():
                dd_info, _ = self.project.get_data_distribution()
                imgui.set_tooltip(f"Num. samples: {dd_info[self.project.collections[collection_id].name]['tot']}\nSplit Ratio: {dd_info[self.project.collections[collection_id].name]['ratio']:.2f}%")
            
            if collection_open:
                imgs = self.project.get_images(collection_id)
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
                        
                    """ if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                        frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                        frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [self.image_data.img_info.w, self.image_data.img_info.h]

                    frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [self.image_data.img_info.scaled_w, self.image_data.img_info.scaled_h]
             """
                for i, img_info in enumerate(imgs):

                    # img_info = project.imgs[k]
                    name = img_info.name
                    clicked, _ = imgui.selectable(
                                label=name + (" OK" if len(img_info.bboxes) > 0 else "") , selected=(state.idx == i and state.collection_id == collection_id)
                            )

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
                            
                        """ if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                            frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                            frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [img_data["img_info"].w, img_data["img_info"].h]

                        frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [img_data["img_info"].scaled_w, img_data["img_info"].scaled_h]
                        """
                    
                imgui.tree_pop()

        imgui.end_child()
        imgui.same_line(position=self.x_offset)
