
from cvlab.gui.app import App
from cvlab.gui.base import Component

import imgui

from cvlab.gui.sections.annotation import Annotator

class Home(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)

        self.annotation_screen = Annotator(self.app)


    def main(self):
        
        self.__header()
    

    def __header(self, ):
    
        if imgui.begin_tab_bar("sections"):

            if imgui.begin_tab_item("LAB")[0]:

                self.annotation_screen.main()
                
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
