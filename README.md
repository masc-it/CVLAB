# CVLAB [WIP]

CVLAB is a computer vision annotation tool written in python. [pyimgui](https://github.com/pyimgui/pyimgui) has been adopted for the graphical user interface. 

My goal is to realize a simple, lightweight and standalone app that let you annotate your images, run auto-annotation experiments with your own models, import/export data collections and analyse your data distribution.

Right now the project is a work in progress. Fundamental features are available and operative, but not ready for a daily usage yet.

![Labels & Info section](https://github.com/masc-it/CVLAB/raw/main/docs/screen_info.PNG)
*Above: Settings & Info section. Allows you to setup your labels and visualize stats about your data.*

## Install from PyPI (Windows only)

    pip install cvlab-gui

## Installation requirements
## pyimgui
Yolo-LAB runs on the docking branch of PyImgui (not on PyPI atm). You can install the provided wheels.
### windows
    pip install *win_amd64.whl

### linux
    pip install *linux_x86_64.whl

## other requirements
    pip install -r requirements.txt
	pip install -r yolov5/requirements.txt

# Setup new project
    python -m cvlab_gui.setup_project

# Run CVLAB GUI
    python -m cvlab_gui.main