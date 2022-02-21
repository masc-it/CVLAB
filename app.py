#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
backend = "glfw"

import glfw
from imgui.integrations.glfw import GlfwRenderer

import OpenGL.GL as gl
from stb import image as im
import imgui

from components import home, projects
import ctypes
import custom_utils
from variables import frame_data


myappid = 'mascit.app.yololab' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def setup_images():
    global frame_data

    imgs = ["annotate_preview", "inference_preview"]
    for i in imgs:
        frame_data["imgs_to_render"][i] = {
            "prev_name": "",
            "name": "",
            "texture": None,
            "scale": 1.0,
            "img_info" : None
        }


def main_glfw():
    global frame_data
    def glfw_init():
        width, height = 1024, 900
        window_name = "YoloV5 GUI"
        if not glfw.init():
            print("Could not initialize OpenGL context")
            exit(1)
        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
        glfw.window_hint(glfw.REFRESH_RATE, 60)
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
    window = glfw_init()
    impl = GlfwRenderer(window)
    io = impl.io
    frame_data["glfw"] = {"io": io, "window": window}
    x = im.load('chip.png')
    glfw.set_window_icon(window, 1, [(x.shape[1],x.shape[0], x)])
    
    io.fonts.clear()
    font_scaling_factor = custom_utils.fb_to_window_factor(window)
    io.font_global_scale = 1. / font_scaling_factor
    
    io.fonts.add_font_from_file_ttf("Roboto-Regular.ttf", 18, io.fonts.get_glyph_ranges_latin())
    impl.refresh_font_texture()
    
    frame_data["io"] = imgui.get_io()

    setup_images()
    
    frame_data["projects"] = projects.load_projects()

    # test
    project : projects.Project = frame_data["projects"][0]
    frame_data["project"]  = project

    project.init_project()
    #project.load_annotations()
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        custom_utils.load_images(frame_data["imgs_to_render"])
       
        imgui.new_frame()
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
    global frame_data

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", 'Cmd+Q', False, True
            )
            if clicked_quit:
                exit(1)
            imgui.end_menu()
        imgui.end_main_menu_bar()
    viewport = imgui.get_main_viewport().size
    frame_data["viewport"] = viewport
    imgui.set_next_window_size(viewport[0], viewport[1]-25, condition=imgui.ALWAYS)
    imgui.set_next_window_position(0, 25, condition=imgui.ALWAYS)
    flags = ( imgui.WINDOW_NO_MOVE 
        | imgui.WINDOW_NO_TITLE_BAR
        |   imgui.WINDOW_NO_COLLAPSE
        | imgui.WINDOW_NO_RESIZE
        
    )
    
    imgui.begin("Custom window", None, flags=flags)
    
    home.header()

    imgui.end()



if __name__ == "__main__":
    imgui.create_context()

    io = imgui.get_io()
    
    backend = "glfw"
    main_glfw()
    