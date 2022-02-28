import imgui
from components.data import Labels
from components.projects import Project
from variables import frame_data
from array import array

def settings_labels(labels : Labels):

    global frame_data
    
    imgui.dummy(10,10)
    imgui.push_font(frame_data["fonts"]["roboto_large"])
    imgui.text(" Labels")
    imgui.pop_font()
    imgui.begin_table("labels_t", 4, outer_size_height=0, flags=imgui.TABLE_SIZING_STRETCH_SAME|imgui.TABLE_RESIZABLE)

    imgui.table_setup_column("INDEX", )
    imgui.table_setup_column("LABEL",)
    imgui.table_setup_column("COLOR",)
    imgui.table_setup_column("SHORTCUT",)

    imgui.table_headers_row()
    
    for label_obj in labels:
        imgui.table_next_row()
        imgui.table_set_column_index(0)
        imgui.text(str(label_obj.index))
        imgui.table_set_column_index(1)
        imgui.push_item_width(-1)
        _,label_obj.label= imgui.input_text(label=f"lab_{label_obj.index}", value=label_obj.label, buffer_length=128)
        imgui.pop_item_width()
        imgui.table_set_column_index(2)
        
        _, label_obj.rgb = imgui.color_edit3(
                f"edit_{label_obj.index}", *label_obj.rgb, flags=
                    imgui.COLOR_EDIT_NO_LABEL|imgui.COLOR_EDIT_NO_INPUTS|imgui.COLOR_EDIT_INPUT_RGB
            )
        imgui.table_set_column_index(3)
        imgui.push_item_width(-1)
        short_changed, shortcut= imgui.input_text(label=f"shortcut_{label_obj.index}", value=label_obj.shortcut, buffer_length=2)
        if short_changed:
            try:
                int(shortcut)
                if labels.shortcuts.get(shortcut) is None:
                    del labels.shortcuts[label_obj.shortcut] # del old shortcut
                    label_obj.shortcut = shortcut
                    labels.shortcuts[shortcut] = label_obj
            except:
                pass
            
        imgui.pop_item_width()
            
    imgui.end_table()
    imgui.separator()


def settings_dd():
    global frame_data
    project: Project = frame_data["project"]

    info_dd, tot_samples = project.get_data_distribution()

    imgui.dummy(10,10)
    imgui.push_font(frame_data["fonts"]["roboto_large"])
    imgui.text(" Data distribution")
    imgui.pop_font()

    imgui.text(f"Tot. number of samples: {tot_samples}")

    imgui.begin_table("table_labels_dd", 3,outer_size_height=0, flags=imgui.TABLE_SIZING_STRETCH_SAME)

    imgui.table_setup_column("Collection", )
    imgui.table_setup_column("Num. of samples",)
    imgui.table_setup_column("% Ratio",)

    imgui.table_headers_row()

    for k in info_dd:
        o = info_dd[k]
        imgui.table_next_row()
        imgui.table_set_column_index(0)
        imgui.text(k)
        imgui.table_set_column_index(1)
        imgui.text(str(o["tot"]))
        imgui.table_set_column_index(2)
        imgui.text("%.2f" % o["ratio"])
    
    imgui.end_table()
    imgui.separator()


def settings_label_distribution():
    global frame_data
    project: Project = frame_data["project"]

    label_counts = project.get_labels_distribution()

    imgui.dummy(10,10)
    imgui.push_font(frame_data["fonts"]["roboto_large"])
    imgui.text(" Labels distribution")
    imgui.pop_font()
    imgui.plot_histogram("##labels_dd", 
        array('f', list(label_counts.values())),
        graph_size=(imgui.get_main_viewport().size.x, 300), 
        scale_min=0.0)
    
    num_classes = len(list(label_counts.keys()))
    size_per_item = imgui.get_main_viewport().size.x / num_classes

    labels = list(label_counts.keys())

    imgui.columns(num_classes, "label_names", False)
    for i, l in enumerate(labels):

        t_size = imgui.calc_text_size(l).x

        rem_size = (size_per_item - t_size - 8)*0.5

        imgui.dummy(width=rem_size, height=10)
        imgui.same_line(spacing=0)
        imgui.text(l)
        #imgui.same_line()
        imgui.next_column()
    
    imgui.separator()
