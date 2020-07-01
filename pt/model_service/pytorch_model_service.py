from .model_service import SingleNodeService

from .. import log

logger = log.getLogger(__name__)


class PTServingBaseService(SingleNodeService):

    def __init__(self, model_name, model_path):
        self.model_name = model_name
        self.model_path = model_path
        self.model = None

    def _inference(self, data):

        result = {}
        for k, v in data.items():
            result[k] = self.model(v)

        return result

    def _preprocess(self, data):
        return data

    def _postprocess(self, data):
        return data

    def ping(self):
        return

    def signature(self):
        pass
