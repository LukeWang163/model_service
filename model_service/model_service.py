# coding:utf-8
from abc import ABCMeta, abstractmethod

import log

logger = log.getLogger(__name__)


class ModelService(object):
    """ModelService wraps up all preprocessing, inference and postprocessing
    functions used by model service. It is defined in a flexible manner to
    be easily extended to support different frameworks.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.ctx = None

    @abstractmethod
    def inference(self, data):
        pass


class SingleNodeService(ModelService):
    """SingleNodeModel defines abstraction for model service which loads a
    single model.
    """

    def inference(self, source_data):
        input_data = self._read_data(source_data)
        preprocessed_data = self._preprocess(input_data)
        inference_result = self._inference(preprocessed_data)
        result_data = self._postprocess(inference_result)
        return result_data

    @abstractmethod
    def _read_data(self, data):
        return data

    @abstractmethod
    def _inference(self, data):
        return data

    @abstractmethod
    def _preprocess(self, data):
        return data

    @abstractmethod
    def _postprocess(self, data):
        return data
