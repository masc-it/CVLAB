import imgui
from components.data import Labels
from variables import frame_data
def settings_labels(labels : Labels):

    global frame_data
    
    imgui.begin_child(label="labels_table", height=250, border=False, )
    imgui.push_font(frame_data["fonts"]["roboto_large"])
    imgui.text(" Labels")
    imgui.pop_font()
    imgui.begin_table("labels_t", 4, flags=imgui.TABLE_SIZING_STRETCH_SAME|imgui.TABLE_RESIZABLE)

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
    imgui.end_child()


def settings_data_distribution():
    pass