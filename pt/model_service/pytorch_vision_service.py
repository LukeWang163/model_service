from .pytorch_model_service import PTServingBaseService


class PTServingVisionService(PTServingBaseService):

    def _preprocess(self, data):
        return data

    def _postprocess(self, data):
        return data

    def ping(self):
        return

    def signature(self):
        pass
