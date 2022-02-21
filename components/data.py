from copy import deepcopy
from PIL import Image
from __future__ import annotations

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

    def scale(self, in_size, out_size):
        bbox = self.as_array()
        x_scale = float(out_size[0]) / in_size[0]
        y_scale = float(out_size[1]) / in_size[1]

        # xmin, ymin
        bbox[0] = x_scale * bbox[0]
        bbox[2] = y_scale * bbox[2]

        # xmax, ymax
        bbox[1] = x_scale * bbox[1]
        bbox[3] = y_scale * bbox[3]

        return bbox


class ImageInfo(object):

    bboxes : list[BBox] = []
    prev_scale = 0.0
    scale = 1.0
    is_changed = False
    def __init__(self, name, path) -> None:
        self.name = name
        self.path = path
        self._set_size()
    
    def add_bbox(self, bbox: BBox):
        self.bboxes.append(bbox)
    
    def add_bboxes(self, bboxes: list[BBox]):
        self.bboxes.extend(bboxes)
    
    def _set_size(self):
        img = Image.open(self.path)
        self.w = img.size[0]
        self.h = img.size[1]
    
    def change_scale(self, scale: float):

        self.prev_scale = self.scale
        self.scale = scale
        scaled_w = int(self.w*scale)
        scaled_h = int(self.h*scale)
        self.scaled_w = scaled_w
        self.scaled_h = scaled_h

        for bbox in self.bboxes:
            bbox = bbox.scale((self.w, self.h), (scaled_w, scaled_h))

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
    
    shortcuts : dict[str, LabelInfo] = {}

    def add_label(self, label: LabelInfo):
        self.labels.append(label)

        self.shortcuts[label.shortcut] = label

    def __getitem__(self, i):
        return self.labels[i]
    
    
    