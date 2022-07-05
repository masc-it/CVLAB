import imgui
import threading
from components.data import BBox, ImageInfo

from components.projects import Project


def update_ds_split_count(frame_data):
    project : Project = frame_data["project"]
    ds_split_map = {
        0: [], # train
        1: [], # test
        2: []  # validation
    }

    for coll_info in frame_data["export_table"]:

        coll_target_split : list[int] = frame_data["export_table"][coll_info]
        try:
            ds_split_map[coll_target_split.index(1)].extend(list(project.imgs[coll_info.id].values()))
        except:
            pass
    
    #print(ds_split_map)
    frame_data["export_counts"] = frame_data["project"].get_num_imgs(ds_split_map)

    return ds_split_map


def export_process(frame_data, ):

    ds_split_map = update_ds_split_count(frame_data)

    for i, (coll_name, _) in enumerate(frame_data["project"].export(ds_split_map)):
        frame_data["export_progress"] = i+1
        frame_data["export_collection"] = coll_name
    frame_data["export_running"] = False

def show_export_modal(frame_data,):

    if imgui.begin_popup_modal("Export progress",  )[0]: # imgui.WINDOW_NO_RESIZE

        frame_data["is_dialog_open"] = True
        imgui.begin_table("export_t", 4, outer_size_height=0, flags=imgui.TABLE_SIZING_STRETCH_SAME|imgui.TABLE_RESIZABLE)

        imgui.table_setup_column("Collection", )
        imgui.table_setup_column("Train",)
        imgui.table_setup_column("Test",)
        imgui.table_setup_column("Validation",)

        imgui.table_headers_row()

        project : Project = frame_data["project"]
        if frame_data["export_table"] == {}:
            for i, coll in enumerate(project.collections.values()):
                frame_data["export_table"][coll] = [False] * 3
                #if i <= 2:
                #    frame_data["export_table"][coll][i] = True
                if "train" in coll.name.lower():
                    frame_data["export_table"][coll][0] = True
                else:
                    frame_data["export_table"][coll][2] = True
        
        if frame_data["export_counts"] == {}:
            update_ds_split_count(frame_data)

        for coll in project.collections.values():

            imgui.table_next_row()
            imgui.table_set_column_index(0)
            imgui.text(coll.name)
            for i, el in enumerate(["train", "test", "validation"]):
                imgui.table_set_column_index(i+1)
                if imgui.radio_button(f"##exp_table{coll.name}_{el}", frame_data["export_table"][coll][i]):
                    frame_data["export_table"][coll] = [False] * 3
                    frame_data["export_table"][coll][i] = True
                    update_ds_split_count(frame_data)
        
        imgui.table_next_row()
        tot = frame_data["export_counts"]["tot"]

        for i, split in enumerate(frame_data["export_counts"]["splits"]):
            imgui.table_set_column_index(i+1)
            count = frame_data["export_counts"]["splits"][split]
            imgui.text(f"Samples: {count}\nRatio: {count/tot*100:.2f}%")
        

        imgui.end_table()

        #print(imgui.get_content_region_available())
        imgui.dummy(10, imgui.get_content_region_available().y - 30)
        #imgui.set_cursor_pos_y(imgui.get_content_region_available().y - 30)
        export_clicked = imgui.button("Export")
        if export_clicked:
            frame_data["export_running"] = True
            export_t = threading.Thread(target=export_process, args=(frame_data,))
            export_t.start()

        if frame_data["export_running"] and frame_data["export_collection"] is not None:
            collection_name = frame_data["export_collection"]
            index = frame_data["export_progress"]
            total = frame_data["export_counts"]["splits"][collection_name]
            imgui.text(f"{collection_name}: {index}/{total}")
            imgui.progress_bar(index / total, size=(-1, 0.0),)
        
        
        imgui.same_line()
        close_clicked = imgui.button("Close")
        if close_clicked:
            frame_data["export_collection"] = None
            frame_data["is_dialog_open"] = False
            imgui.close_current_popup()
        imgui.end_popup()


def show_label_selection(frame_data, bbox: BBox, img_info : ImageInfo):

    if imgui.begin_popup_modal("Label", flags=imgui.WINDOW_NO_RESIZE )[0]: # imgui.WINDOW_NO_RESIZE
        project : Project = frame_data["project"]
        imgui.begin_child(label="labels_listt", width=300, height=500, border=False, )

        for label in project.labels:
            #print(i)
            clicked, _ = imgui.selectable(
                                label=label.label , selected=(bbox.label == label.index)
                            )
            if clicked:
                bbox.label = label.index
                img_info.set_changed(True)
                frame_data["is_dialog_open"] = False
                frame_data["is_editing"] = False
                imgui.close_current_popup()
        imgui.end_child()
        imgui.end_popup()