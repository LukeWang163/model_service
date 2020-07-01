from PIL import Image
import numpy as np
from tf.model_service.tfserving_model_service import TfServingBaseService


class mnist_service(TfServingBaseService):

    def _preprocess(self, data):
        preprocessed_data = {}

        images = []
        for k, v in data.items():
            for file_name, file_content in v.items():
                image1 = Image.open(file_content)
                image1 = np.array(image1, dtype=np.float32)
                image1.resize((1, 784))
                images.append(image1)

        images = np.array(images,dtype=np.float32)
        images.resize((len(data), 784))
        preprocessed_data['images'] = images

        return preprocessed_data

    def _postprocess(self, data):

        infer_output = {"mnist_result": []}
        for output_name, results in data.items():

            for result in results:
                infer_output["mnist_result"].append(result.index(max(result)))

        return infer_output
