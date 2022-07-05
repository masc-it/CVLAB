
from cvlab.model.app import App
from cvlab.gui.base import Component

import imgui

from cvlab.gui.sections.annotation import Annotator
from cvlab.gui.sections.data_info import DataInfo
from cvlab.gui.sections.settings import Settings

class Home(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)

        self.annotation_screen = Annotator(self.app)

        self.data_info_screen = DataInfo(self.app)
        self.settings_screen = Settings(self.app)


    def main(self):
        
        self.__header()
    

    def __header(self, ):
    
        if imgui.begin_tab_bar("sections"):

            if imgui.begin_tab_item("LAB")[0]:

                self.annotation_screen.main()
                
                imgui.end_tab_item()
            
            if imgui.begin_tab_item("Data Info")[0]:

                imgui.begin_child(label="datainfo_section", border=False, )
                
                self.data_info_screen.main()

                imgui.end_child()
                imgui.end_tab_item()

            if imgui.begin_tab_item("Settings")[0]:

                imgui.begin_child(label="setting_section", border=False, )
                
                self.settings_screen.main()

                imgui.end_child()
                imgui.end_tab_item()
            imgui.end_tab_bar()
