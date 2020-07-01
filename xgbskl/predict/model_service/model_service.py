# coding:utf-8
from abc import ABCMeta, abstractmethod

from . import log

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
        list_data = self._preprocess(source_data)
        pre_result = self._inference(list_data)
        post_result = self._postprocess(pre_result)
        return post_result

    @abstractmethod
    def _inference(self, data):
        return data

    @abstractmethod
    def _preprocess(self, data):
        return data

    @abstractmethod
    def _postprocess(self, pre_data):
        return pre_data
