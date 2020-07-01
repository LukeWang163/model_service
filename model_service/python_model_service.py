# -*- coding: utf-8 -*-
import collections
import json
import traceback
import base64
from json import JSONEncoder
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.externals import joblib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import log
from model_service import SingleNodeService

logger = log.getLogger(__name__)


class SklearnServingBaseService(SingleNodeService):

    def __init__(self, model_path):
        self.model_path = model_path

    def _read_data(self, data):
        logger.info("Parsing data from user input")
        data_frame = pd.read_json(data, orient="split", dtype=False, precise_float=False)
        return data_frame

    def _preprocess(self, data):
        logger.info("Do no pre-processing by default")
        return data

    def _inference(self, data):
        inference_result = predict(self.model_path, data)
        return inference_result

    def _postprocess(self, data):
        logger.info("Process inference result")
        result = StringIO()
        predictions_to_json(data, result)
        return result


def predict(model_path, pre_data):

    try:
        logger.info("Try to load sklearn model...")
        load_model = joblib.load(model_path)
    except:
        try:
            logger.info("Try to load xgboost model...")
            load_model = xgb.Booster(model_file=model_path)
            pre_data = xgb.DMatrix(pre_data)
        except:
            logger.error("Model type is not supported!")
            logger.error(traceback.format_exc())
            raise

    try:
        pre_result = load_model.predict(pre_data)
        pre_result = pre_result.tolist()
        return pre_result
    except:
        logger.error('Predict failed!')
        logger.error(traceback.format_exc())
        raise


def predictions_to_json(raw_predictions, output):
    predictions = _get_jsonable_obj(raw_predictions, pandas_orient="records")
    json.dump(predictions, output, cls=NumpyEncoder)


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