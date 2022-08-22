
from cvlab.model.app import App
from cvlab.gui.base import Component

import imgui
from array import array

class DataInfo(Component):

    def __init__(self, app: App) -> None:
        super().__init__(app)
    
    def main(self):
        
        self.__labels_distribution()
        self.__data_distribution()


    def __labels_distribution(self):

        label_counts = self.project.get_labels_distribution()

        imgui.begin_child(label="labels_dd_section", height=400, border=False, )
        imgui.dummy(10,10)
        imgui.push_font(self.app.fonts["roboto_large"])
        imgui.text(" Labels distribution")
        imgui.pop_font()
        imgui.plot_histogram("##labels_dd", 
            array('f', list(label_counts.values())),
            graph_size=(self.app.viewport.x, 300), 
            scale_min=0.0)
        
        num_classes = len(list(label_counts.keys()))
        size_per_item = self.app.viewport.x / num_classes

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
        imgui.end_child()
    
    def __data_distribution(self):

        info_dd, tot_samples = self.project.get_data_distribution()
        
        imgui.dummy(10,10)
        imgui.push_font(self.app.fonts["roboto_large"])
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
