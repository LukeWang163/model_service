from PIL import Image
import numpy as np


from .tfserving_model_service import TfServingBaseService


class TfServingVisionService(TfServingBaseService):
    def _preprocess(self, data):
        preprocessed_data = {}
        for k, v in data.items():
            images = []
            for file_name, file_content in v.items():
                image1 = Image.open(file_content)
                image1 = image1.convert("RGB")
                image1 = np.array(image1, dtype=np.float32)
                image1 = image1[:, :, :]
                images.append(image1.tolist())

            preprocessed_data[k] = images
        return preprocessed_data
