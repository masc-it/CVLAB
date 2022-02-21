
from __future__ import annotations
import os, glob, json,sys
from copy import deepcopy
from components.data import BBox, ImageInfo, LabelInfo, Labels
sys.path.append("./")  # add ROOT to PATH
import custom_utils

class Project(object):
    
    page_status = {}

    def __init__(self, name, info_obj) -> None:
        self.name = name
        self.info_obj = info_obj
        self.paths = info_obj["paths"]
        self.model_path = info_obj["model_path"]
        self.labels_obj = info_obj["labels"]
        self.imgs : dict[str,ImageInfo] = {}
        self.labels : Labels = self.load_labels()

    def __str__(self) -> str:
        return json.dumps(self.info_obj, indent=1)
    
    def init_project(self):
        for p in self.paths:
            data_path = p["data"]
            ext_ann_path = p["ext_annotations"]
            self.import_annotations(data_path, ext_ann_path)
        
        
    def import_annotations(self, data_path, yolo_annotations_path):

        for f in glob.glob(f"{yolo_annotations_path}/*.txt"):
            name = os.path.basename(f).rsplit('.')[0]

            img_path = f"{data_path}/{name}.jpg"
            img_info = ImageInfo(name, img_path)
            bboxes = custom_utils.import_yolo_predictions(f, img_info.w, img_info.h)

            img_info.add_bboxes(bboxes)
            self.imgs[name] = img_info
            
            if not os.path.exists(f"projects/{self.name}/annotations/{name}.json"):
                bboxes_list = list(map(lambda x: x.as_obj(), bboxes))
                with open(f"projects/{self.name}/annotations/{name}.json", "w") as fp:
                    data = {"img_path": img_path, "bboxes": bboxes_list}
                    json.dump(data, fp, indent=1)
    
    def load_annotations(self, ):

        for f in glob.glob(f"projects/{self.name}/annotations/*.json"):
            name = os.path.basename(f).rsplit('.')[0]
            with open(f, "r") as fp:
                data = json.load(fp)
            
            img_path = data["img_path"]

            bboxes = list(map(lambda x: BBox(x["xmin"],x["ymin"],x["xmax"],x["ymax"], x["label"], x["conf"]), data["bboxes"]))
            img_info = ImageInfo(name, img_path)
            
            img_info.add_bboxes(bboxes)
            self.imgs[name] = img_info
        

    def get_image(self):
        for img in self.imgs:
            yield self.imgs[img]

    def load_labels(self):

        labels = Labels()
        for k in self.info_obj["labels"]:
            obj = self.info_obj["labels"][k]
            l = LabelInfo(
                obj["index"], 
                obj["label"],
                [ color / 255.0 for color in obj["rgb"]],
                obj["shortcut"])
            labels.add_label(l)
        return labels
    
    def update_labels(self, save=True):

        labels_obj = {}
        for o in self.labels:
            labels_obj[o.index] = o.as_obj(rgb_int=True)
        
        self.info_obj["labels"] = labels_obj
        if save:
            self.save_config()

    def save_config(self):
        with open(f"projects/{self.name}/info.json", "w") as fp:
            json.dump(self.info_obj, fp, indent=1)

    def load_json_annotation(self, img_name):

        with open(f"projects/{self.name}/annotations/{img_name}.json", "r") as fp:
            annotations = json.load(fp)
        
        return annotations
    
    def set_changed(self, img_name):

        self.page_status[img_name] = True

    def save_annotations(self,):
        
        for img_info in self.imgs.values():
            
            if img_info.is_changed:
                with open(f"projects/{self.name}/annotations/{img_info.name}.json", "w") as fp:
                    scaled_bboxes = []
                    for bbox in img_info.bboxes:
                        scaled_bboxes.append(bbox.scale((img_info.scaled_w, img_info.scaled_h), (img_info.w, img_info.h)).as_obj())
                    data = {"img_path": img_info.path, "bboxes": scaled_bboxes}
                    json.dump(data, fp, indent=1 )
                img_info.set_changed(False)


def load_projects():

    projects = []
    for p in glob.glob("projects/*"):
        
        with open(p + "/info.json", "r") as fp:
            info_obj = json.load(fp)
        projects.append(Project(os.path.basename(p), info_obj))
    
    return projects


if __name__ == "__main__":
    for p in load_projects():
        print(p)