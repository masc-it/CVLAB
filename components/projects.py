import imgui

import os, glob, json,sys

sys.path.append("./")  # add ROOT to PATH
import custom_utils

class Project(object):

    def __init__(self, name, info_obj) -> None:
        self.name = name
        self.info_obj = info_obj
        self.paths = info_obj["paths"]
        self.model_path = info_obj["model_path"]
        self.labels = info_obj["labels"]
        self.imgs = {}

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
            img_size = custom_utils.get_image_size(img_path)
            bboxes = custom_utils.import_yolo_predictions(f, img_size[0], img_size[1])
            self.imgs[img_path] = {}
            with open(f"projects/{self.name}/annotations/{name}.json", "w") as fp:
                json.dump(bboxes, fp, indent=1)

    def get_pair(self):
        for img in self.imgs:
            if self.imgs[img].get("size") is None:
                self.imgs[img]["orig_size"] = custom_utils.get_image_size(img)
            self.imgs[img]["name"] = os.path.basename(img).rsplit('.')[0]
            if self.imgs[img].get("bboxes") is None:
                self.imgs[img]["bboxes"] = self.load_json_annotation(self.imgs[img]["name"])

            yield self.imgs[img]

    def load_json_annotation(self, img_name):

        with open(f"projects/{self.name}/annotations/{img_name}.json", "r") as fp:
            annotations = json.load(fp)
        
        return annotations


def get_projects():

    projects = []
    for p in glob.glob("projects/*"):
        # print(os.path.basename(p))
        with open(p + "/info.json", "r") as fp:
            info_obj = json.load(fp)
        projects.append(Project(os.path.basename(p), info_obj))
    
    return projects




if __name__ == "__main__":
    for p in get_projects():
        print(p)