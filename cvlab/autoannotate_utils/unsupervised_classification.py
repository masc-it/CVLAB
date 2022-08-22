import math
from pathlib import Path
from typing import Any, Tuple, Union
import onnx
import faiss
from PIL import Image
import torchvision.transforms as T
import onnxruntime
import numpy as np

from cvlab.model.data import ImageInfo

np.random.seed(42)

class PseudoClassifier(object):

    def __init__(self, onnx_model_path : Path, kb_path: Path, input_size : int = 128, features_size = 1024 ) -> None:
        
        self.input_size = input_size
        self.kb_path = kb_path
        self.val_trfs = T.Compose([
            T.Resize(
                size=(input_size, input_size), interpolation=T.InterpolationMode.BICUBIC
            ),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.kb = []
        self.labels = []
        self.kb_dict = {}

        self.similarity = FeatureSimilarity(dim=features_size)

        self.imgs_path = (self.kb_path / "imgs")

        self.imgs_path.mkdir(exist_ok=True)
        if len(list(self.kb_path.glob("*.npz"))) > 0:
            self.kb, self.labels, self.kb_dict = self.load_kb()
            self.similarity.fit(np.array(self.kb, dtype=np.float32))
        
            print(f"Features in DB: {len(self.kb)}")

        onnx_model = onnx.load(onnx_model_path.as_posix())
        onnx.checker.check_model(onnx_model)
        session_option = onnxruntime.SessionOptions()
        session_option.enable_mem_pattern = False
        self.onnx_model = onnxruntime.InferenceSession(onnx_model_path.as_posix(), sess_options=session_option, providers=['DmlExecutionProvider', 'CPUExecutionProvider'])

    @staticmethod 
    def to_numpy(tensor):
        return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

    def load_kb(self):
        
        features_dict = {}
        features = []
        labels = []
        for features_file in self.kb_path.glob("*.npz"):
            data = np.load(features_file)
            features_dict[features_file.stem] = {"features": data["features"].tolist(), "labels": data["labels"].tolist()}

            names = []
            with open((self.kb_path / features_file.stem).with_suffix(".txt"), "r") as fp:
                for l in fp.readlines():
                    names.append(l.strip())
            features_dict[features_file.stem]["img_names"] = names

            features.extend(features_dict[features_file.stem]["features"])
            labels.extend(features_dict[features_file.stem]["labels"])
        
        return features, labels, features_dict

    def save_kb(self):
        
        for img_name, obj in self.kb_dict.items():
            self.save_kb_single(img_name)
    
    def save_kb_single(self, img_name):

        obj = self.kb_dict[img_name]
        features = np.array(obj["features"])
        labels = np.array(obj["labels"])
        p = (self.kb_path / img_name).with_suffix(".npz")
        np.savez_compressed(p, features=features, labels=labels)
        p_txt = (self.kb_path / img_name).with_suffix(".txt")

        with open(p_txt, "w") as fp:
            for img_name in obj["img_names"]:
                fp.write(img_name + "\n")

    def add_img_to_kb(self, parent_name: str, img_path: Path, label: int):

        img = Image.open(img_path).convert("RGB")
        
        feature_vector = self.predict(img)[0][0]
        # save to image .npz
        img_name = img_path.stem
        
        if self.kb_dict.get(parent_name) is None:
            self.kb_dict[parent_name] = {"features" : [], "labels": [], "img_names": []}

        self.kb.append(feature_vector)
        self.labels.append(label)

        self.kb_dict[parent_name]["features"].append(feature_vector)
        self.kb_dict[parent_name]["labels"].append(label)
        self.kb_dict[parent_name]["img_names"].append(img_name)
        # update faiss DB
        self.similarity.fit(np.array([feature_vector]))

    def knn(self, neighbor_idxs: np.ndarray):

        counts = {}

        for i in neighbor_idxs:
            
            if i == -1:
                continue
            label = self.labels[i]
            if counts.get(label) is None:
                counts[label] = 0
            counts[label] += 1
        
        return max(counts, key=lambda key: counts[key])


    def predict_label(self, img_path: Any):

        if len(self.kb) == 0:
            return None
        
        if isinstance(img_path, Path):
            img = Image.open(img_path).convert("RGB")
        elif isinstance(img_path, Image.Image):
            img = img_path
        else:
            return -1, None, None
        feature_vector = self.predict(img)[0][0]

        distances, neighbors = self.similarity.find_nearest_to_query(np.array([feature_vector]), k = 10)

        return self.knn(neighbors.flatten()), distances, neighbors


    def predict(self, img: Image):
        img = self.val_trfs(img)
        img.unsqueeze_(0)

        img = PseudoClassifier.to_numpy(img)
        ort_inputs = {self.onnx_model.get_inputs()[0].name: img}
        ort_outs = self.onnx_model.run(None, ort_inputs)
        return ort_outs
    
    def add_bboxes_to_kb(self, img_info: ImageInfo ):

        """
            Update knowledge base given an image.
            - Generate and save image crops from bounding boxes
            - Generate related feature vectors
        """

        img_info_path = Path(img_info.path)

        img = Image.open(img_info_path).convert("RGB")
        if img_info.w is None:
            img_info._set_size()
        for i, bbox in enumerate(img_info.bboxes):
            random_name = f"{img_info.collection_info.name}_{img_info_path.stem}_{i}_{bbox.label}"
            crop_path = (self.imgs_path / random_name ).with_suffix(".jpg")

            if crop_path.exists():
                continue
            scaled_bbox = bbox.scale((img_info.w, img_info.h), (img_info.orig_w, img_info.orig_h))
            crop = img.crop((math.ceil(scaled_bbox.xmin), math.ceil(scaled_bbox.ymin), math.ceil(scaled_bbox.xmax), math.ceil(scaled_bbox.ymax)))
            
            crop.save(crop_path)

            # update faiss index
            self.add_img_to_kb( f"{img_info.collection_info.name}_{img_info_path.stem}", crop_path, bbox.label)

        if len(img_info.bboxes) > 0:
            self.save_kb_single(f"{img_info.collection_info.name}_{img_info_path.stem}")
        # print("kb saved")
    

class FeatureSimilarity(object):
    
    def __init__(self, dim: int) -> None:
        
        self.dim = dim
        self.index = faiss.index_factory(self.dim, "Flat", faiss.METRIC_INNER_PRODUCT )
        #self.index = faiss.IndexFlatL2(self.dim)
        
    """
        Output:
        - 1st ndarray contains squared distances between the query vector and the neighbors
        - 2nd ndarray is a matrix where the i-th row contains the neighbors of the i-th query vector
    """

    def fit(self, new_vector: np.ndarray):
        faiss.normalize_L2(new_vector)
        self.index.add(new_vector)

    def find_nearest_to_query(self, query : np.ndarray, k : int = 4) -> Tuple[np.ndarray, np.ndarray]:
        faiss.normalize_L2(query)
        return self.index.search(query, k)
