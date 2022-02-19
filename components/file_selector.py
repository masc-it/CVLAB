import glob
import os
from os import getcwd
import imgui

prev_dir = ""
curr_dir = getcwd()
files = {}

history = {
    "i": 0,
    "history": [getcwd()]
}

file_selected_idx = -1
file_selected = None

def get_files(dir):

    global files

    if files.get(dir) is not None:
        return files.get(dir)
    
    files[dir] = glob.glob(dir + "/*")

    return files[dir]
    

def file_selector(title, directory=False):
    global curr_dir
    global prev_dir
    global history
    global file_selected_idx,file_selected
    imgui.set_next_window_size(600, 380)
    if imgui.begin_popup_modal(title, flags=imgui.WINDOW_NO_RESIZE )[0]:
        
        _, curr_dir = imgui.input_text(
                label="", value=curr_dir, buffer_length=400
            )
        
        clicked_back = imgui.button("<")

        if clicked_back:
            
            history["i"] += 1
            curr_dir = "/".join(os.path.split(curr_dir)[:-1])
            if curr_dir not in history["history"]:
                history["history"].append(curr_dir)
        
        imgui.same_line()
        clicked_next = imgui.button(">")

        if clicked_next:

            if history["i"] > 0:
                history["i"] -= 1
            
                curr_dir = history["history"][history["i"]]
        imgui.begin_child(label="files_modal", height=250, border=False, )
        imgui.columns(3)
        for i, p in enumerate(get_files(curr_dir)):
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
                    history["history"].append(curr_dir)
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