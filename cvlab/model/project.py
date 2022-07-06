
from __future__ import annotations
import math
import os, glob, json
from pathlib import Path
from cvlab.model.data import *
from typing import Generator, Any
import zipfile
from io import BytesIO
from collections import namedtuple

from tqdm.auto import tqdm

import cvlab.gui.custom_utils as custom_utils

CVLAB_PROJECTS_DIR = "cvlab_projects/"

class Project(object):
    
    def __init__(self, name:str, info_obj: list[str], project_path:str, fast_load = True) -> None:
        
        self.preload_metadata = not fast_load
        self.name = name
        self.info_obj = info_obj
        self.collections_obj : list[str] = info_obj["collections"]
        
        self.od_model_path = info_obj["od_model_path"] if info_obj["od_model_path"] != "" else None
        
        self.pseudo_classifier = None

        if info_obj["pseudo_classifier"] != {}:
            PseudoClassifier = namedtuple("PseudoClassifier", "model_path kb_path features_shape")

            self.pseudo_classifier = PseudoClassifier(
                info_obj["pseudo_classifier"]["model_path"], 
                info_obj["pseudo_classifier"]["kb_path"],
                info_obj["pseudo_classifier"]["features_shape"]
            )

        self.labels_obj = info_obj["labels"]
        self.project_path = project_path
        
        self.setup_project()
        
    def __str__(self) -> str:
        return json.dumps(self.info_obj, indent=1)
    
    def setup_project(self, init = False):
        self.imgs : dict[str, dict[str, ImageInfo]]  = {}
        self.collections : dict[str, CollectionInfo]= {}
        self.labels : Labels = self.load_labels()
        self.experiments : dict[str, Experiment] = {}
        #self.load_experiments()

        if init:
            self.init_project()

    def init_project(self):
        
        print(f"\nLABELS: {list(map(lambda x: x.label, self.labels))}")

        print("\nInit images metadata...")
        for base_dir in self.collections_obj:

            base_dir_path = Path(base_dir)

            dirs = list(filter(lambda x: x.is_dir(), base_dir_path.glob("*")))

            pbar = tqdm(dirs)
            for dir in pbar:
                
                pbar.set_postfix({"collection": base_dir, "dir": dir.stem})
                data_path : Path = dir
                collection_name = dir.stem
                collection_id = collection_name.replace(" ", "_")

                coll_info = CollectionInfo(collection_name, collection_id, data_path.as_posix())
                self.collections[collection_id] = coll_info
                self.imgs[collection_id] = {}

                (data_path / "annotations/").mkdir(exist_ok=True)

                # init imgs dict with imgs in data_path
                for f in data_path.glob("*.jpg"):
                    img_name = f.stem
                    img_ext = f.suffix.replace(".", "")
                    self.imgs[collection_id][img_name] = ImageInfo(img_name, img_ext, coll_info)
        
        if self.preload_metadata:
            self.load_annotations()
     
    
    def get_collection(self, collection_id: str) -> CollectionInfo:
        return self.collections[collection_id]
    
    def import_yolo_annotations(self, data_path, yolo_annotations_path):

        for f in glob.glob(f"{yolo_annotations_path}/*.txt"):
            name = os.path.basename(f).rsplit('.')[0]

            img_path = f"{data_path}/{name}.jpg"
            img_info = ImageInfo(name, img_path)
            bboxes = custom_utils.import_yolo_predictions(f, img_info.w, img_info.h)

            img_info.add_bboxes(bboxes)
            self.imgs[name] = img_info
            
            ann_path = (Path( CVLAB_PROJECTS_DIR ) / self.name / "annotations" / name).with_suffix(".json")
            if not ann_path.exists():
                bboxes_list = list(map(lambda x: x.as_obj(), bboxes))
                with open(ann_path, "w") as fp:
                    data = {"img_path": img_path, "bboxes": bboxes_list}
                    json.dump(data, fp, indent=1)
    
    def load_annotations(self, ):

        for collection in tqdm(self.collections.values()):

            annotations_dir = Path(collection.path) / "annotations"

            if not annotations_dir.exists():
                continue
            for annotation in annotations_dir.glob("*.json"):
                img_name = annotation.stem
                img_info : ImageInfo = self.imgs[collection.id][img_name]

                with open(annotation, "r") as fp:
                    data = json.load(fp)

                bboxes = list(map(lambda x: BBox(x["xmin"],x["ymin"],x["xmax"],x["ymax"], x["label"], x["conf"]), data["bboxes"]))

                img_info.add_bboxes(bboxes)
    
    def load_image_annotations(self, collection: CollectionInfo, img_name:str):
        
        img_info : ImageInfo = self.imgs[collection.id][img_name]

        annotation_file = f"{collection.path}/annotations/{img_name}.json"
        if not os.path.exists(annotation_file):
            return
        with open(annotation_file, "r") as fp:
            data = json.load(fp)

        bboxes = list(map(lambda x: BBox(x["xmin"],x["ymin"],x["xmax"],x["ymax"], x["label"], x["conf"]), data["bboxes"]))

        img_info.add_bboxes(bboxes)

    def get_image(self, collection_id) -> Generator[ImageInfo, Any, Any]:
        for img in self.imgs[collection_id]:
            yield self.imgs[collection_id][img]
    
    def get_images(self, collection_id) -> list[ImageInfo]:
        d = self.imgs[collection_id]

        return list(d.values())

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
        cfg_file_path = (Path(CVLAB_PROJECTS_DIR) / self.name / "info").with_suffix(".json")
        with open(cfg_file_path, "w") as fp:
            json.dump(self.info_obj, fp, indent=1)

    def load_json_annotation(self, img_name : str):

        ann_path = (Path( CVLAB_PROJECTS_DIR ) / self.name / "annotations" / img_name).with_suffix(".json")
        with open(ann_path, "r") as fp:
            annotations = json.load(fp)
        
        return annotations
    
    def save_annotations(self,):
        
        for collection in self.collections.values():
            for img_name in self.imgs[collection.id]:
                img_info : ImageInfo = self.imgs[collection.id][img_name]
                if img_info.is_changed:
                    p = f"{collection.path}/annotations/{img_name}.json"
                    print(f"SAVED: {p}")
                    with open(p, "w") as fp:
                        scaled_bboxes = []
                        for bbox in img_info.bboxes:
                            scaled_bboxes.append(bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h)).as_obj())
                        data = {"collection": collection.id, "bboxes": scaled_bboxes}
                        json.dump(data, fp, indent=1 )
                    img_info.set_changed(False)

    def save_all_bounding_boxes(self, out_path: Path):

        out_path.mkdir(exist_ok=True)

        for collection in self.collections.values():
            for img_name in self.imgs[collection.id]:
                img_info : ImageInfo = self.imgs[collection.id][img_name]

                img = Image.open(img_info.path).convert("RGB")
                img_path = Path(img_info.path)
                for i, bbox in enumerate(img_info.bboxes):

                    class_name = self.labels.labels_map[bbox.label].label 
                    random_name = f"{collection.name}_{img_path.stem}_{i}"
                    p_dir = (out_path / class_name)
                    p_dir.mkdir(exist_ok=True)

                    crop_path = (p_dir / random_name ).with_suffix(".jpg")

                    crop = img.crop((math.ceil(bbox.xmin), math.ceil(bbox.ymin), math.ceil(bbox.xmax), math.ceil(bbox.ymax)))
                    crop.save(crop_path)

                print(f"SAVED -{img_info.path}")


    """ def save_settings(self):

        labels = list(map(lambda x : x.as_obj(), self.labels))

        with open(f"{self.project_path}/info.json", "w") as fp:
            json.dump(self.) """

    def load_experiments(self):
        
        with open(f"{self.project_path}/experiments.json", "r") as fp:
            exp_obj =json.load(fp)
        
        for exp_key in exp_obj:
            exp = Experiment(exp_obj[exp_key]["model_path"], exp_obj[exp_key]["data_path"], exp_key) 
            self.experiments[exp_key] = exp
            exp._load_images()
        
        return self.experiments

    def save_experiment(self, exp: Experiment):
        self.experiments[exp.exp_name] = exp
        with open(f"{self.project_path}/experiments.json", "r") as fp:
            exp_obj = json.load(fp)
        exp_obj[exp.exp_name] = {
            "data_path" : exp.data_path,
            "model_path": exp.model_path
        }

        with open(f"{self.project_path}/experiments.json", "w") as fp:
            json.dump(exp_obj, fp, indent=1)
        
    def get_labels_distribution(self):

        counts = {
            l.label:0 for l in self.labels
        }

        for collection in self.collections.values():
            for img_name in self.imgs[collection.id]:
                img_info : ImageInfo = self.imgs[collection.id][img_name]

                for bbox in img_info.bboxes:
                    counts[ self.labels.labels_map[bbox.label].label] += 1
        
        return counts

    def get_data_distribution(self):

        info = {
            collection.name:{} for collection in self.collections.values()
        }

        tot = 0
        for collection in self.collections.values():
            imgs = list(filter(lambda x: len(x.bboxes)> 0, self.imgs[collection.id].values()))
            l = len(imgs)
            
            info[collection.name]["tot"] = l
            tot += l
            
        for collection in self.collections.values():
            info[collection.name]["ratio"] = info[collection.name]["tot"] / tot * 100 if tot > 0 else 0

        return info, tot

    def get_num_imgs(self, ds_split_map: dict[int, list[ImageInfo]]):

        info = { "splits": {}, "tot": 0}
        splits = ["train", "test", "validation"]

        for i in ds_split_map:

            paths = ds_split_map[i]
            info["splits"][splits[i]] = len(paths)
            info["tot"] += len(paths)

        return info

    def export(self, ds_split_map: dict[int, list[ImageInfo]]):

        def image2byte_array(path):
            imgByteArr = BytesIO()
            image = Image.open(path).convert("RGB")
            image.save(imgByteArr, format='JPEG')
            imgByteArr = imgByteArr.getvalue()
            return imgByteArr
        
        from PIL import Image
        
        zf = zipfile.ZipFile(self.project_path + "/export.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)
        
        splits = ["train", "test", "validation"]
        for i in ds_split_map:

            imgs = ds_split_map[i]

            for img in imgs:
                
                if len(img.bboxes) == 0:
                    continue
                img_bytes = image2byte_array(img.path)
                
                zf.writestr( f"dataset/{splits[i]}/images/{img.collection_info.name}_{img.name}.{img.ext}", img_bytes)
                zf.writestr( f"dataset/{splits[i]}/labels/{img.collection_info.name}_{img.name}.txt", img.export_bboxes())
              
                yield splits[i]

        zf.close()


    @staticmethod
    def load_projects(fast_load:bool) -> list[Project]:

        _projects = []
        for p in Path(CVLAB_PROJECTS_DIR).glob("*"):
            
            if not p.is_dir():
                continue

            with open(p / "info.json", "r") as fp:
                info_obj = json.load(fp)
            _projects.append(Project(p.stem, info_obj, p.as_posix(), fast_load=fast_load))
        
        return _projects
    
    @staticmethod
    def setup_new_project():
        print("Project Name -> ", end = "")
        project_name = input()

        projects_dir = Path(CVLAB_PROJECTS_DIR)
        project_dir = (projects_dir / project_name)

        try:
            project_dir.mkdir(parents=True)
        except:
            print("Project name already exists.")
            return

        print("Data collection paths (comma separated) -> ", end = "")
        collections = input().split(",")

        for collection in collections:
            coll = Path(collection)
            if not coll.exists():
                print(f"{coll.as_posix()} does NOT exist.")
                return
        print("Number of classes -> ", end = "")
        num_classes = int(input())
        num_classes = max(1, num_classes)

        labels = {}
        """
        "labels": {
            "0": {
            "index": "0",
            "label": "A",
            "rgb": [
                235,
                64,
                52
            ],
            "shortcut": "1"
            },
        """
        for i in range(num_classes):
            label = {
                "index": str(i),
                "label": "A",
                "rgb": [
                    235,
                    64,
                    52
                ],
                "shortcut": str(i+1) if i < 9 else ""
            }
            labels[str(i)] = label
        
        print("Object detection model path (Enter to skip) -> ", end = "")
        od_model_path = input()
        if not od_model_path:
            od_model_path = ""
        
        print("ONNX Classification model path (Enter to skip) -> ", end = "")
        classifier_path = input()
        pseudo_classifier = {}
        if classifier_path:
            pseudo_classifier["model_path"] = classifier_path
            print("Knowledge base path -> ", end = "")
            pseudo_classifier["kb_path"] = input()
            print("Features shape -> ", end = "")
            pseudo_classifier["features_shape"] = int(input())

        info_obj = {
            "collections": collections,
            "od_model_path": od_model_path,
            "pseudo_classifier": pseudo_classifier,
            "labels": labels
        }

        with open( (project_dir / "info.json"), "w" ) as fp:
            json.dump(info_obj, fp, indent=2)
        
        print(f"{project_name} has been successfully setup. You can customize your labels directly in CVLAB.")

def load_projects2(project_base_path):

    projects = []
    for p in Path(project_base_path).glob("*"):
        
        with open(p / "info.json", "r") as fp:
            info_obj = json.load(fp)
        projects.append(Project(os.path.basename(p), info_obj, p))
    
    return projects

if __name__ == "__main__":
    for p in Project.load_projects():
        print(p)