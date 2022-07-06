import json
from pathlib import Path
import time
import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
backend = "glfw"
import argparse
import glfw
from imgui.integrations.glfw import GlfwRenderer

import OpenGL.GL as gl
from stb import image as im
import imgui

from cvlab.model.project import Project

import cvlab
from cvlab.model.app import App
from cvlab.gui.sections.home import Home
from cvlab.autoannotate_utils.unsupervised_classification import PseudoClassifier
from cvlab.gui.dialogs.export import ExportDatasetDialog

if sys.platform == "win32":
    import ctypes
    myappid = 'mascit.app.cvlab'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

base_p = Path(os.path.dirname(cvlab.__file__))
gui_data = base_p / "gui_data/"

app = App()

home = None

exportDialog = None

def fb_to_window_factor(window):
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)

    return max(float(fb_w) / win_w, float(fb_h) / win_h)


def main_glfw(args):
    global app
    global home
    global exportDialog

    def glfw_init():
        width, height = 1024, 900
        window_name = "CVLAB"
        if not glfw.init():
            print("Could not initialize OpenGL context")
            exit(1)
        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
        glfw.window_hint(glfw.REFRESH_RATE, 60)
        glfw.window_hint(glfw.MAXIMIZED, True)
        # Create a windowed mode window and its OpenGL context
        window = glfw.create_window(
            int(width), int(height), window_name, None, None
        )

        glfw.make_context_current(window)
        if not window:
            glfw.terminate()
            print("Could not initialize Window")
            exit(1)
        return window


    print("Initializing...")
    projects = Project.load_projects(args.fast_load)
    
    for i, project in enumerate(projects):
        print(f"{i+1} - {project.name}", end="\n", flush=True)
    
    print("Project index -> ", end="")

    proj_idx = int(input())

    proj_idx = max(1, proj_idx)
    app.project : Project = projects[proj_idx-1]
    app.project.init_project()

    if app.project.pseudo_classifier is not None:
        print("Loading Pseudo Classifier..")
        app.classifier = PseudoClassifier(
            Path(app.project.pseudo_classifier.model_path),
            kb_path = Path(app.project.pseudo_classifier.kb_path),
            features_size = app.project.pseudo_classifier.features_shape
        )

    imgui.create_context()
    io = imgui.get_io()
    #io.config_flags |= imgui.CONFIG_DOCKING_ENABLE

    window = glfw_init()
    impl = GlfwRenderer(window)
    io = impl.io

    app.glfw = {"io": io, "window": window, "previous_cursor": glfw.ARROW_CURSOR}

    x = im.load((gui_data /'chip.png').as_posix())
    glfw.set_window_icon(window, 1, [(x.shape[1],x.shape[0], x)])
    
    io.fonts.clear()
    font_scaling_factor = fb_to_window_factor(window)
    io.font_global_scale = 1. / font_scaling_factor
    
    # default font
    font_config = imgui.FontConfig(oversample_h=2.0, oversample_v=2.0, rasterizer_multiply=0.9)
    io.fonts.add_font_from_file_ttf( (gui_data / "Roboto-Regular.ttf").as_posix(), 18, font_config, io.fonts.get_glyph_ranges_default())

    # headers font
    roboto_large = io.fonts.add_font_from_file_ttf(
        (gui_data / "Roboto-Regular.ttf").as_posix(), 30, imgui.FontConfig(oversample_h=2.0, oversample_v=2.0 )
    )
    app.fonts["roboto_large"] = roboto_large

    impl.refresh_font_texture()
    
    app.io = imgui.get_io()


    home = Home(app)
    exportDialog = ExportDatasetDialog(app)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        # load image textures if needed
        # this must be done before the on_frame call
        app.load_images()
       
        imgui.new_frame()
        viewport = imgui.get_main_viewport().size
        app.viewport = viewport

        on_frame()
        
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
        time.sleep(0.0013)

    impl.shutdown()
    glfw.terminate()


# backend-independent frame rendering function:

def on_frame():
    global app
    global home
    global exportDialog
    
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_reload, _ = imgui.menu_item(
                "Reload", None, False, True
            )
            if clicked_reload:
                app.project.setup_project(init=True)
                home = Home(app)
                exportDialog = ExportDatasetDialog(app)
            
            clicked_export, _ = imgui.menu_item(
                "Export", None, False, True
            )
            if clicked_export:
                app.export_dialog_click = True
            
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", 'Cmd+Q', False, True
            )
            if clicked_quit:
                exit(1)
                
            imgui.end_menu()
        imgui.end_main_menu_bar()
    
    
    imgui.set_next_window_size(app.viewport[0], app.viewport[1]-25, condition=imgui.ALWAYS)
    imgui.set_next_window_position(0, 25, condition=imgui.ALWAYS)
    flags = ( imgui.WINDOW_NO_MOVE 
        | imgui.WINDOW_NO_TITLE_BAR
        |   imgui.WINDOW_NO_COLLAPSE
        | imgui.WINDOW_NO_RESIZE 
    )
    
    imgui.begin("Custom window", None, flags=flags)
    if app.export_dialog_click:
        app.export_dialog_click = False
        imgui.open_popup("Export progress")
        imgui.set_next_window_size(600, 600)
    
    exportDialog.main()
    
    home.main()

    imgui.end()



def docking_space(name: str):
    flags = (imgui.WINDOW_MENU_BAR 
        | imgui.WINDOW_NO_DOCKING 
        # | imgui.WINDOW_NO_BACKGROUND
        | imgui.WINDOW_NO_TITLE_BAR
        | imgui.WINDOW_NO_COLLAPSE
        | imgui.WINDOW_NO_RESIZE
        | imgui.WINDOW_NO_MOVE
        | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        | imgui.WINDOW_NO_NAV_FOCUS
    )

    viewport = imgui.get_main_viewport()
    x, y = viewport.pos
    w, h = viewport.size
    imgui.set_next_window_position(x, y)
    imgui.set_next_window_size(w, h)

    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)

    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (0, 0))
    imgui.begin(name, None, flags)
    imgui.pop_style_var()
    imgui.pop_style_var(2)

    # DockSpace
    dockspace_id = imgui.get_id(name)
    imgui.dockspace(dockspace_id, (0, 0), imgui.DOCKNODE_PASSTHRU_CENTRAL_NODE)

    imgui.end()

if __name__ == "__main__":
    
    backend = "glfw"

    parser = argparse.ArgumentParser("CVLAB")

    parser.add_argument("--fast_load", action="store_true", help="Optimize loading time when data is served over the network. Lazy load of image annotations and metadata. Data info ")
    
    args = parser.parse_args()
    main_glfw(args)
    