import sys
from components.data import BBox
from components.projects import Project
from components import projects as p


def get_iou(bbox1:BBox, bbox2: BBox):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    Returns
    -------
    float
        in [0, 1]
    """

    # determine the coordinates of the intersection rectangle
    x_left = max(bbox1.xmin, bbox2.xmin)
    y_top = max(bbox1.ymin, bbox2.ymin)
    x_right = min(bbox1.xmax, bbox2.xmax)
    y_bottom = min(bbox1.ymax, bbox2.ymax)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    bb1_area = (bbox1.xmax - bbox1.xmin) * (bbox1.ymax - bbox1.ymin)
    bb2_area = (bbox2.xmax - bbox2.xmin) * (bbox2.ymax - bbox2.ymin)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)

    return iou

def check_overlapping_boxes(base_path):
    projects = p.load_projects2(base_path)

    # test
    project : Project = projects[0]
    print(project.name)

    project.init_project()

    for collection_id in project.collections:
        imgs = project.get_images(collection_id)

        for img in imgs:

            bboxes = img.bboxes

            for bbox in bboxes:
                others = list(filter(lambda x: x != bbox, bboxes))
                same = list(filter(lambda x: (x.xmin == bbox.xmin and x.ymin == bbox.ymin) or ( bbox.xmin >= x.xmin and bbox.ymin >= x.ymin and bbox.xmax <= x.xmax and bbox.ymax <= x.ymax ) or ( bbox.xmin <= x.xmin and bbox.ymin <= x.ymin and bbox.xmax >= x.xmax and bbox.ymax >= x.ymax ) or get_iou(bbox, x) > 0.6, others))

                if len(same) > 0:
                    print(f"{img.collection_info.name} - {img.name} has overlapping bbox")

