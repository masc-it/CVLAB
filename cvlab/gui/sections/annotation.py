
from cvlab.gui.app import App, FileList, Image, Labeling
from cvlab.gui.base import Component

import imgui
import glfw

class Annotator(Component):
    
    def __init__(self, app: App, ) -> None:
        super().__init__(app)

        self.scroll_right_margin = 60

        self.labeling = Labeling()

        self.auto_annotate = False

        self.image_data = app.image_data

        self.scroll_right_margin = 60
        
        self.img_render_id = "home"

        self.file_list_state = FileList()
    

    def main(self):
        self.x_offset = int(self.app.viewport[0] / 5) + self.app.padding

        self.__options_menu()
        self.__files_list()
        self.__annotator()

    def __options_menu(self, ):
        
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
                    
                    self.image_data.has_changed = True
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
                        
                        self.image_data.has_changed = True
                        """ if frame_data["imgs_info"].get(frame_data["selected_file"]["name"]) is None:
                            frame_data["imgs_info"][frame_data["selected_file"]["name"]] = {}
                            frame_data["imgs_info"][frame_data["selected_file"]["name"]]["orig_size"] = [img_data["img_info"].w, img_data["img_info"].h]

                        frame_data["imgs_info"][frame_data["selected_file"]["name"]]["scaled_size"] = [img_data["img_info"].scaled_w, img_data["img_info"].scaled_h]
                        """
                    
                imgui.tree_pop()

        imgui.end_child()
        imgui.same_line(position=self.x_offset)
    

    def __annotator(self):
        
        imgui.begin_child(label="img_preview", width=0, height=0, border=False, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR )
        
        padding = 8

        if self.image_data.texture is not None and self.image_data.img_info.scaled_w > imgui.get_content_region_available().x:
            padding = 22 # 8 + 14 = h_scrollbar height
        
        self.app.y_offset = self.app.viewport.y - imgui.get_content_region_available().y - padding # frame_data["y_offset_auto_ann"]
        if self.image_data.texture is not None:
            imgui.image(self.image_data.texture, self.image_data.img_info.scaled_w, self.image_data.img_info.scaled_h)
        
        imgui.end_child()

        return
        draw_list : imgui._DrawList = imgui.get_window_draw_list()
        
        if self.image_data.texture is not None and frame_data["is_editing"] == False and (frame_data["io"].mouse_pos[0] <= frame_data["x_offset"] or \
        frame_data["io"].mouse_pos[1] <= frame_data["y_offset"] or frame_data["io"].mouse_pos[1] >= img_data["scaled_height"] + frame_data["y_offset"]) :
            labeling["was_mouse_down"] = False
            labeling["new_box_requested"] = False
            labeling["curr_bbox"] = None
        # new bbox requested, was drawing a box and mouse is released => save bbox
        if labeling["curr_bbox"] is not None and frame_data["is_editing"] == False and allow_edit and labeling["was_mouse_down"] and labeling["new_box_requested"] and not imgui.is_mouse_down() :
            labeling["was_mouse_down"] = False
            #labeling["new_box_requested"] = False
            labeling["curr_bbox"].width = abs(labeling["curr_bbox"].xmax - labeling["curr_bbox"].xmin)
            labeling["curr_bbox"].height = abs(labeling["curr_bbox"].ymax - labeling["curr_bbox"].ymin)

            if frame_data["autoannotate"] == True:
                autoannotate(frame_data, labeling["curr_bbox"], img_info)
            else:
                img_info.bboxes.append(labeling["curr_bbox"])
                img_info.set_changed(True)
                #if labeling["curr_bbox"] is not None:
            
            auto_classify(frame_data, labeling["curr_bbox"], img_info)
            if frame_data["autoclassifier"] != -1:
                labeling["curr_bbox"].label = frame_data["autoclassifier"]
                frame_data["autoclassifier"] = -1
            
            labeling["curr_bbox"] = None
            if frame_data["autoannotate"]:
                frame_data["autoannotate"] = False
                labeling["new_box_requested"] = False
                
        # draw bbox following mouse coords
        elif allow_edit and not frame_data["is_dialog_open"] and imgui.is_mouse_down() and labeling["new_box_requested"]:

            labeling["was_mouse_down"] = True
            curr_bbox : BBox = labeling["curr_bbox"]
            if curr_bbox is None:
                # save coords relative to the image, not app 
                curr_bbox = BBox(
                    frame_data["io"].mouse_pos[0] - frame_data["x_offset"] + imgui.get_scroll_x(),
                    frame_data["io"].mouse_pos[1] - frame_data["y_offset"] + imgui.get_scroll_y(),
                    0,
                    0,
                    frame_data["labeling"]["selected_label"]
                )
                labeling["curr_bbox"] = curr_bbox
            
            curr_bbox.xmax = frame_data["io"].mouse_pos[0] - frame_data["x_offset"] + imgui.get_scroll_x()
            curr_bbox.ymax = frame_data["io"].mouse_pos[1] - frame_data["y_offset"] + imgui.get_scroll_y() 
            # convert image coords to screen coords

            # prevent to draw boxes right-2-left
            __check_bbox(curr_bbox, frame_data, img_info)

            if curr_bbox.xmax - curr_bbox.xmin > MIN_BBOX_SIZE and\
            curr_bbox.ymax - curr_bbox.ymin > MIN_BBOX_SIZE : # bboxes must have at least 5px width/height
                draw_list.add_rect(
                    curr_bbox.xmin + frame_data["x_offset"] - imgui.get_scroll_x(), 
                    curr_bbox.ymin +  frame_data["y_offset"] - imgui.get_scroll_y() , 
                    curr_bbox.xmax + frame_data["x_offset"] - imgui.get_scroll_x(), 
                    curr_bbox.ymax  +  frame_data["y_offset"] - imgui.get_scroll_y(), 
                    imgui.get_color_u32_rgba(*project.labels.labels_map[curr_bbox.label].rgb, 255), 
                    thickness=1)
                img_info.set_changed(True)
        else: # draw bboxes and handle interaction
            
            if img_info is not None:
                
                _refresh_bboxes(frame_data, labeling, project, draw_list, img_render_id)
            
            if allow_edit and not frame_data["is_dialog_open"]:
                _handle_bbox_drag(frame_data, labeling,img_info)
                _handle_bbox_resize(frame_data, labeling,img_info)
                
                # remove bbox shortcut
                if imgui.is_key_pressed(glfw.KEY_BACKSPACE) and labeling["curr_bbox"] is not None:
                    img_info.bboxes.remove(labeling["curr_bbox"])
                    labeling["curr_bbox"] = None
                    img_info.set_changed(True)            
                    
                for i in project.labels.shortcuts:
                    if i == "":
                        continue
                    if imgui.is_key_pressed(int(i)+glfw.KEY_0) : 
                        frame_data["labeling"]["selected_label"] = project.labels.shortcuts[i].index
                        if labeling["curr_bbox"] is not None:
                            labeling["curr_bbox"].label = project.labels.shortcuts[i].index
                            img_info.set_changed(True)
                        break
                
                if labeling["curr_bbox"] is not None:
                    l = project.labels.labels_map[labeling['curr_bbox'].label].label
                    imgui.set_tooltip(f"Label: {l}")

                if imgui.is_key_pressed(glfw.KEY_TAB) and labeling["curr_bbox"] is not None:
                    
                    imgui.open_popup("Label")
                    imgui.set_next_window_size(350, 600)
                    frame_data["is_editing"] = True
                    frame_data["is_dialog_open"] = True
                
                """ if imgui.is_key_pressed(glfw.KEY_C) and labeling["curr_bbox"] is not None:
                    auto_classify(frame_data, labeling["curr_bbox"], img_info) """
                
                # duplicate bbox
                if imgui.is_key_pressed(glfw.KEY_D) and labeling["curr_bbox"] is not None:
                    
                    labeling["new_box_requested"] = False
                    xmin = labeling["curr_bbox"].xmax + 3
                    xmax = xmin + labeling["curr_bbox"].width

                    bbox_copy = BBox(
                        xmin,
                        labeling["curr_bbox"].ymin,
                        xmax,
                        labeling["curr_bbox"].ymax,
                        labeling["curr_bbox"].label
                    )
                    img_info.bboxes.append(bbox_copy)
                
                if imgui.is_key_pressed(glfw.KEY_SPACE) and labeling["curr_bbox"] is not None:
                    auto_classify(frame_data, labeling["curr_bbox"], img_info)
                    if frame_data["autoclassifier"] != -1:
                        labeling["curr_bbox"].label = frame_data["autoclassifier"]
                        frame_data["autoclassifier"] = -1

                if not imgui.is_mouse_down(0) and not imgui.is_mouse_down(1) and frame_data["is_dialog_open"] == False and frame_data["is_editing"] == False:
                    labeling["curr_bbox"] = None
            
            show_label_selection(frame_data, labeling["curr_bbox"], img_info)
            
        imgui.end_child()