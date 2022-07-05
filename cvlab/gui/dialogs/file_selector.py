import glob
import os
from os import getcwd
import imgui

from cvlab.gui.base import Component
from cvlab.model.app import App

class FileSelector(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)

        self.prev_dir = ""
        self.curr_dir = getcwd()
        self.files = {}

        self.history = {
            "i": 0,
            "history": [getcwd()]
        }

        self.file_selected_idx = -1
        self.file_selected = None

    def main(self, title : str, canSelectDir : bool = False):
        
        self.show_file_selector(title, canSelectDir)

    def show_file_selector(self, title, directory=False):

        imgui.set_next_window_size(600, 380)
        if imgui.begin_popup_modal(title, flags=imgui.WINDOW_NO_RESIZE )[0]:
            
            _, curr_dir = imgui.input_text(
                    label="", value=curr_dir, buffer_length=400
                )
            
            clicked_back = imgui.button("<")

            if clicked_back:
                
                self.history["i"] += 1
                curr_dir = "/".join(os.path.split(curr_dir)[:-1])
                if curr_dir not in self.history["history"]:
                    self.history["history"].append(curr_dir)
            
            imgui.same_line()
            clicked_next = imgui.button(">")

            if clicked_next:

                if self.history["i"] > 0:
                    self.history["i"] -= 1
                
                    curr_dir = self.history["history"][self.history["i"]]
            imgui.begin_child(label="files_modal", height=250, border=False, )
            imgui.columns(3)
            for i, p in enumerate(self.__get_files(curr_dir)):
                clicked, _ = imgui.selectable(
                            label=os.path.basename(p), selected=(file_selected_idx == i),
                            flags=imgui.SELECTABLE_DONT_CLOSE_POPUPS
                        )
                if clicked:
                    
                    file_selected = str(p)
                    if os.path.isdir(file_selected):
                        curr_dir = file_selected
                        if not directory:
                            file_selected = ""
                        self.history["history"].append(curr_dir)
                    else:
                        file_selected_idx = i
                imgui.next_column()
            imgui.end_child()
            imgui.columns(1)
            if imgui.button(label="Confirm", width=120, height=0):
                imgui.close_current_popup()
                imgui.end_popup()
                file_selected_idx = -1
                return file_selected
            imgui.same_line()
            if imgui.button(label="Cancel", width=120, height=0):
                imgui.close_current_popup()

            imgui.end_popup()

        return None
    
    def __get_files(self, dir):

        if self.files.get(dir) is not None:
            return self.files.get(dir)
        
        self.files[dir] = glob.glob(dir + "/*")

        return self.files[dir]
        