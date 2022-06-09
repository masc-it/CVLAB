import json
from pathlib import Path


annots_files = Path("D:\\Download\\cocostuff_val\\entity_detector\\train\\annotations\\").glob("*.json")


for ann_file in annots_files:

    with open(ann_file, "r") as fp:
        annotations : list = json.load(fp)
    
    res = []
    for ann in annotations["bboxes"]: 
        if ann["xmin"] < 0 or ann["ymin"] < 0 or ann["xmax"] < 0 or ann["ymax"] < 0:
            continue

        res.append(ann)
    
    obj = {
        "collection": annotations["collection"],
        "bboxes": res
    }
    with open(ann_file, "w") as fp:
        json.dump(obj, fp, indent=2)
    
