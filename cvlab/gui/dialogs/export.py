
import threading
from cvlab.gui.base import Component
from cvlab.model.app import App

import imgui

class ExportDatasetDialog(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)

        self.export_table = {}
        self.export_counts = {}

        self.export_progress = 0
        self.export_running = False

        self.export_collection_name = None

    def main(self):
        self.show_export_modal()


    def show_export_modal(self,):

        if imgui.begin_popup_modal("Export progress",  )[0]: # imgui.WINDOW_NO_RESIZE

            self.app.is_dialog_open = True
            imgui.begin_table("export_t", 4, outer_size_height=0, flags=imgui.TABLE_SIZING_STRETCH_SAME|imgui.TABLE_RESIZABLE)

            imgui.table_setup_column("Collection", )
            imgui.table_setup_column("Train",)
            imgui.table_setup_column("Test",)
            imgui.table_setup_column("Validation",)

            imgui.table_headers_row()

            if self.export_table == {}:
                for i, coll in enumerate(self.project.collections.values()):
                    self.export_table[coll] = [False] * 3
                    #if i <= 2:
                    #    frame_data["export_table"][coll][i] = True
                    if "train" in coll.name.lower():
                        self.export_table[coll][0] = True
                    else:
                        self.export_table[coll][2] = True
            
            if self.export_counts == {}:
                self.__update_ds_split_count()

            for coll in self.project.collections.values():

                imgui.table_next_row()
                imgui.table_set_column_index(0)
                imgui.text(coll.name)
                for i, el in enumerate(["train", "test", "validation"]):
                    imgui.table_set_column_index(i+1)
                    if imgui.radio_button(f"##exp_table{coll.name}_{el}", self.export_table[coll][i]):
                        self.export_table[coll] = [False] * 3
                        self.export_table[coll][i] = True
                        self.__update_ds_split_count()
            
            imgui.table_next_row()
            tot = self.export_counts["tot"]

            for i, split in enumerate(self.export_counts["splits"]):
                imgui.table_set_column_index(i+1)
                count = self.export_counts["splits"][split]
                imgui.text(f"Samples: {count}\nRatio: {count/tot*100:.2f}%")
            

            imgui.end_table()

            #print(imgui.get_content_region_available())
            imgui.dummy(10, imgui.get_content_region_available().y - 30)
            #imgui.set_cursor_pos_y(imgui.get_content_region_available().y - 30)
            export_clicked = imgui.button("Export")
            if export_clicked:
                self.export_running = True
                export_t = threading.Thread(target=self.export_process,)
                export_t.start()

            if self.export_running and self.export_collection_name is not None:
                collection_name = self.export_collection_name
                index = self.export_progress
                total = self.export_counts["splits"][collection_name]
                imgui.text(f"{collection_name}: {index}/{total}")
                imgui.progress_bar(index / total, size=(-1, 0.0),)
            
            imgui.same_line()
            close_clicked = imgui.button("Close")
            if close_clicked:
                self.export_counts = {}
                self.export_table = {}
                self.export_progress = 0
                self.export_collection_name = None
                self.app.is_dialog_open = False
                imgui.close_current_popup()
            imgui.end_popup()

    
    def __update_ds_split_count(self,):
        
        ds_split_map = {
            0: [], # train
            1: [], # test
            2: []  # validation
        }

        for coll_info in self.export_table:

            coll_target_split : list[int] = self.export_table[coll_info]
            try:
                ds_split_map[coll_target_split.index(1)].extend(list(self.project.imgs[coll_info.id].values()))
            except:
                pass
        
        self.export_counts = self.project.get_num_imgs(ds_split_map)

        return ds_split_map


    def export_process(self, ):

        ds_split_map = self.__update_ds_split_count()

        for i, coll_name in enumerate(self.project.export(ds_split_map)):
            self.export_progress = i+1
            self.export_collection_name = coll_name
        self.export_running = False

