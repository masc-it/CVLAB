from __future__ import annotations

from PIL import Image
from copy import deepcopy
import os, glob


class BBox(object):

    def __init__(self, xmin, ymin, xmax, ymax, label="0", conf=1.0) -> None:
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

        self.update_size()
        
        self.label = label
        self.conf = conf
    
    def update_size(self):
        self.width = abs(self.xmax - self.xmin)
        self.height = abs(self.ymax - self.ymin)

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

    def to_yolo(self, in_size : tuple[int, int], out_size : tuple[int, int],):

        box = self.scale(in_size, out_size).as_array()
        dw = 1./(out_size[0])
        dh = 1./(out_size[1])
        x = (box[0] + box[2])/2.0
        y = (box[1] + box[3])/2.0
        w = box[2] - box[0]
        h = box[3] - box[1]
        x = x*dw
        w = w*dw
        y = y*dh
        h = h*dh
        return (x,y,w,h)

class ImageInfo(object):

    prev_scale = 0.0
    scale = 1.0
    is_changed = False
    def __init__(self, name, extension, collection_info: CollectionInfo) -> None:
        self.name = name
        self.ext = extension
        self.collection_info = collection_info
        self.path = collection_info.path + f"/{self.name}.{extension}"
        self.bboxes : list[BBox] = []

        self.w = None
        # self._set_size()
    
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
    
    def export_bboxes(self, format="yolo"):

        annotations = []
        for i, bbox in enumerate(self.bboxes):
            if bbox.xmin < 0 or bbox.ymin < 0 or bbox.xmax < 0 or bbox.ymax < 0:
                print(f"WARNING: {self.name} - {i}th label is corrupt")
                continue
            yolo_coords = bbox.to_yolo(
                (self.scaled_w, self.scaled_h),
                (self.orig_w, self.orig_h), 
                )
            annotations.append(f'{bbox.label} ' + " ".join([str(a) for a in yolo_coords]) + '\n') #  {bbox.conf}
            # fp.write(f'{bbox["label"]} ' + " ".join([str(a) for a in yolo_coords]) + f' {bbox["conf"]}\n')
        return "".join(annotations)
    
class LabelInfo(object):
    def __init__(self, index : str, label : str, rgb : list[float], shortcut: str) -> None:
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

    def __init__(self) -> None:
        self.labels : list[LabelInfo]= []
        self.labels_map : dict[str, LabelInfo] = {}
        self.shortcuts : dict[str, LabelInfo]= {}

    def add_label(self, label: LabelInfo):
        self.labels.append(label)

        self.labels_map[label.index] = label
        self.shortcuts[label.shortcut] = label

    def __getitem__(self, i):
        return self.labels[i]


class CollectionInfo(object):

    def __init__(self, name: str, id: str, path: str) -> None:
        self.name = name
        self.id = id
        self.path = path
        self.num_imgs = 0
        self.count_imgs()
    
    def count_imgs(self):
        self.num_imgs = glob.glob(self.path + "/*.*")

class Experiment(object):

    i = 0
    def __init__(self, model_path:str, data_path:str, exp_name: str, load_annotations = True) -> None:
        
        self.exp_name = exp_name
        self.model_path = model_path
        self.data_path = data_path
        self.threshold_iou = 0.45
        self.threshold_conf = 0.4

        self.is_running = False
        self.progress = 0.0
        self.imgs : list[ImageInfo] = []
        self.coll_info = CollectionInfo(self.exp_name, self.exp_name, self.data_path)
        self.num_imgs = 0
        # self._load_images(load_annotations)
    
    def update_info(self,):

        self.coll_info = CollectionInfo(self.exp_name, self.exp_name, self.data_path)
        self.num_imgs = len(glob.glob(f"{self.data_path}/*.*"))
        os.makedirs(self.data_path + "/annotations", exist_ok=True)


    def add_image(self, img_info: ImageInfo, load_annotations=False):
        from cvlab.gui.custom_utils import load_img_annotations
        self.imgs.append(img_info)
        if load_annotations:
            load_img_annotations(img_info)
    
    def _load_images(self, load_annotations = True):
        import glob, os
        from cvlab.gui.custom_utils import load_img_annotations
        self.imgs = []
        for img in glob.glob(f"{self.data_path}/*.*"):
            name_ext = os.path.basename(img).rsplit('.')
            img_info = ImageInfo(name_ext[0], name_ext[1], self.coll_info)
            self.imgs.append(img_info)
            if load_annotations:
                load_img_annotations(img_info)
