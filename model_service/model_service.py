# coding:utf-8
from abc import ABCMeta, abstractmethod

import log
import json
import base64
from json import JSONEncoder
import numpy as np
import pandas as pd

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
    def _load_model(self):
        return None

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


def predictions_to_json(raw_predictions):
    predictions = _get_jsonable_obj(raw_predictions, pandas_orient="records")
    return json.dumps(predictions, cls=NumpyEncoder)


def _get_jsonable_obj(data, pandas_orient="records"):
    """Attempt to make the data json-able via standard library.
    Look for some commonly used types that are not jsonable and convert them into json-able ones.
    Unknown data types are returned as is.

    :param data: data to be converted, works with pandas and numpy, rest will be returned as is.
    :param pandas_orient: If `data` is a Pandas DataFrame, it will be converted to a JSON
                          dictionary using this Pandas serialization orientation.
    """
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient=pandas_orient)
    if isinstance(data, pd.Series):
        return pd.DataFrame(data).to_dict(orient=pandas_orient)
    else:  # by default just return whatever this is and hope for the best
        return data


class NumpyEncoder(JSONEncoder):
    """ Special json encoder for numpy types.
    Note that some numpy types doesn't have native python equivalence,
    hence json.dumps will raise TypeError.
    In this case, you'll need to convert your numpy types into its closest python equivalence.
    """

    def try_convert(self, o):
        def encode_binary(x):
            return base64.encodebytes(x).decode("ascii")

        if isinstance(o, np.ndarray):
            if o.dtype == np.object:
                return [self.try_convert(x)[0] for x in o.tolist()]
            elif o.dtype == np.bytes_:
                return np.vectorize(encode_binary)(o), True
            else:
                return o.tolist(), True

        if isinstance(o, np.generic):
            return o.item(), True
        if isinstance(o, bytes) or isinstance(o, bytearray):
            return encode_binary(o), True
        return o, False

    def default(self, o):  # pylint: disable=E0202
        res, converted = self.try_convert(o)
        if converted:
            return res
        else:
            return super().default(o)
