import tensorflow as tf
from .. import log
from ..model_def import model_def
from tensorflow import make_tensor_proto
from tensorflow_serving.apis import predict_pb2

from .model_service import SingleNodeService
from .model_service import get_tf_server_stub

logger = log.getLogger(__name__)


class TfServingBaseService(SingleNodeService):

    def __init__(self, model_name, model_path):
        self.model_name = model_name
        self.model_path = model_path
        self.model = model_def.ModelDef(model_name, model_path)
        self.stub = get_tf_server_stub()

    def _inference(self, data):
        request = predict_pb2.PredictRequest()
        request.model_spec.name = self.model.model_name
        request.model_spec.signature_name = self.model.model_signature

        for k, v in data.items():
            request.inputs[k].CopyFrom(make_tensor_proto(data[k]))

        response = self.stub.Predict(request, 60.0)

        result = {}

        for output_name in response.outputs:
            tensor_proto = response.outputs[output_name]
            result[output_name] = tf.contrib.util.make_ndarray(tensor_proto).tolist()

        return result

    def _preprocess(self, data):

        return data

    def _postprocess(self, data):

        return data

    def ping(self):
        return

    def signature(self):
        pass
