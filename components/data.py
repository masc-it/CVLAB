from __future__ import annotations
from PIL import Image
from copy import deepcopy

class BBox(object):

    def __init__(self, xmin, ymin, xmax, ymax, label="0", conf=1.0) -> None:
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

        self.width = abs(xmax - xmin)
        self.height = abs(ymax - ymin)
        self.label = label
        self.conf = conf
    
    def as_array(self):
        return [self.xmin, self.ymin, self.xmax, self.ymax]
    
    def as_obj(self):
        return {
            "xmin": self.xmin,
            "ymin": self.ymin,
            "xmax": self.xmax,
            "ymax": self.ymax,
            "width": self.width,
            "height": self.height,
            "conf": self.conf,
            "label": self.label
        }

    def scale(self, in_size, out_size):
        bbox = deepcopy(self.as_array())
        x_scale = float(out_size[0]) / float(in_size[0])
        y_scale = float(out_size[1]) / float(in_size[1])

        # xmin, ymin
        bbox[0] = x_scale * bbox[0]
        bbox[1] = y_scale * bbox[1]

        # xmax, ymax
        bbox[2] = x_scale * bbox[2]
        bbox[3] = y_scale * bbox[3]

        return BBox(bbox[0], bbox[1], bbox[2], bbox[3], self.label, self.conf)


class ImageInfo(object):

    bboxes : list[BBox] = []
    prev_scale = 0.0
    scale = 1.0
    is_changed = False
    def __init__(self, name, path) -> None:
        self.name = name
        self.path = path
        self.bboxes = []
        self._set_size()
    
    def add_bbox(self, bbox: BBox):
        self.bboxes.append(bbox)
    
    def add_bboxes(self, bboxes: list[BBox]):
        self.bboxes.extend(bboxes)
    
    def _set_size(self):
        img = Image.open(self.path)
        self.w = img.size[0]
        self.h = img.size[1]
        self.orig_w = img.size[0]
        self.orig_h = img.size[1]
        self.scaled_w = img.size[0]
        self.scaled_h = img.size[1]
    
    def change_scale(self, scale: float):

        if self.scale == scale:
            return
        self.prev_scale = self.scale
        self.scale = scale

        curr_w = deepcopy(self.w)
        curr_h = deepcopy(self.h)

        new_scaled_w = int(self.orig_w*scale)
        new_scaled_h = int(self.orig_h*scale)

        self.w = new_scaled_w
        self.h = new_scaled_h

        self.scaled_w = new_scaled_w
        self.scaled_h = new_scaled_h

        for i, bbox in enumerate(self.bboxes):
            new_bbox = bbox.scale((curr_w, curr_h), (new_scaled_w, new_scaled_h))
            self.bboxes[i].xmin = new_bbox.xmin
            self.bboxes[i].xmax = new_bbox.xmax
            self.bboxes[i].ymin = new_bbox.ymin
            self.bboxes[i].ymax = new_bbox.ymax
            self.bboxes[i].width = abs(self.bboxes[i].xmax - self.bboxes[i].xmin)
            self.bboxes[i].height = abs(self.bboxes[i].ymax - self.bboxes[i].ymin)
        """ print(self.bboxes[0].xmin / new_scaled_w)
        print("end") """


    def set_changed(self, value=True):
        self.is_changed = value

class LabelInfo(object):
    def __init__(self, index : int, label : str, rgb : list[float], shortcut: str) -> None:
        self.index = index
        self.label = label
        self.rgb = rgb
        self.shortcut = shortcut
    
    def as_obj(self, rgb_int=False ):
        return {
            "index": self.index,
            "label": self.label,
            "rgb" : self.rgb if not rgb_int else [int(color*255) for color in self.rgb],
            "shortcut" : self.shortcut
        }

class Labels(object):
    labels : list[LabelInfo] = []
    
    labels_map : dict[str, LabelInfo] = {}
    shortcuts : dict[str, LabelInfo] = {}

    def add_label(self, label: LabelInfo):
        self.labels.append(label)

        self.labels_map[label.index] = label
        self.shortcuts[label.shortcut] = label

    def __getitem__(self, i):
        return self.labels[i]
    
    
    