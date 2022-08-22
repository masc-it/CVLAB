from pathlib import Path
import cv2
import argparse
import json
from pycocotools.coco import COCO

def show(args):

    folder: Path = Path(args.folder)
    
    ann_folder = folder / "annotations"

    for img in folder.glob("*.jpg"):

        ann_file = (ann_folder / img.stem).with_suffix(".json")

        with open(ann_file, "r") as fp:
            ann_obj = json.load(fp)
        
        boxes :list[dict] = ann_obj["bboxes"]

        mat = cv2.imread(img.as_posix())

        for box in boxes:
            mat = cv2.rectangle(mat, (round(box["xmin"]), round(box["ymin"])), (round(box["xmax"]), round(box["ymax"])), (255, 0, 0), 1 )

        cv2.imshow(f"{img.as_posix()}", mat)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def show(args):

    folder: Path = Path(args.folder)
    
    if (folder / "annotations").exists() and len(list(folder.glob("*.jpg"))) > 0: # cvlab
        show_cvlab(folder)
    elif (folder / "annotations").exists() and (folder / "train").exists(): # coco
        show_coco(folder, args.name, args.from_id)
    else: # yolo
        pass
    

def show_coco(folder:Path, name: str, from_id: int = 0):

    ann_folder = folder / "annotations"

    ann_file = (ann_folder / name).with_suffix(".json")

    coco = COCO(ann_file)

    imgs = coco.getImgIds()
    """ for img_id in imgs[from_id:]:
        img = coco.loadImgs(img_id)[0]
        
        img_path = (folder / name / str(img["file_name"]))

        annotations_id = coco.getAnnIds(img_id)

        annotations = coco.loadAnns(annotations_id)
        if len(annotations) == 0:
            print(f"No annotations. {img_path.as_posix()}")
            continue
        mat = cv2.imread(img_path.as_posix())

        ok = False
        for ann in annotations:
            box = ann["bbox"]
            if box[2] <= 5 or box[3] <= 5:
                ok = True
                print(f"Small annots. {img_id} - {img_path.as_posix()}")
                mat = cv2.rectangle(mat, (round(box[0]), round(box[1])), (round(box[0] + box[2]), round(box[1] + box[3])), (255, 0, 0), 1 )

        if ok:
            cv2.imshow(f"{img_id} - {img_path.as_posix()}", mat)
            cv2.waitKey(0)
            cv2.destroyAllWindows() """

    for img_id in imgs[from_id:]:
        img = coco.loadImgs(img_id)[0]
        
        img_path = (folder / name / str(img["file_name"]))
        mat = cv2.imread(img_path.as_posix())

        annotations_id = coco.getAnnIds(img_id)

        annotations = coco.loadAnns(annotations_id)
        if len(annotations) == 0:
            print(f"No annotations. {img_path.as_posix()}")
            continue
        for ann in annotations:
            box = ann["bbox"]
            mat = cv2.rectangle(mat, (round(box[0]), round(box[1])), (round(box[0] + box[2]), round(box[1] + box[3])), (255, 0, 0), 1 )

        cv2.imshow(f"{img_id} - {img_path.as_posix()}", mat)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def show_cvlab(folder:Path):
    ann_folder = folder / "annotations"

    for img in folder.glob("*.jpg"):

        ann_file = (ann_folder / img.stem).with_suffix(".json")

        with open(ann_file, "r") as fp:
            ann_obj = json.load(fp)
        
        boxes :list[dict] = ann_obj["bboxes"]

        mat = cv2.imread(img.as_posix())

        for box in boxes:
            mat = cv2.rectangle(mat, (round(box["xmin"]), round(box["ymin"])), (round(box["xmax"]), round(box["ymax"])), (255, 0, 0), 1 )

        cv2.imshow(f"{img.as_posix()}", mat)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser("Check CVLAB annotations")

    parser.add_argument("--folder", type=str)

    # coco
    parser.add_argument("--name", type=str, default="train")
    parser.add_argument("--from_id", type=int, default=0)
    args = parser.parse_args()
    
    show(args)
