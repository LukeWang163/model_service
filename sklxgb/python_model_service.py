# -*- coding: utf-8 -*-
import traceback
from model_service import SingleNodeService, predictions_to_jsonable
import log
import pandas as pd
import xgboost as xgb

try:
    from sklearn.externals import joblib
except ImportError:
    import joblib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

logger = log.getLogger(__name__)


class SklearnServingBaseService(SingleNodeService):

    def __init__(self, model_path):
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self):
        model = load_model(self.model_path)
        return model

    def _read_data(self, data):
        logger.info("Parsing data from user input")
        data_frame = pd.read_json(data, orient="split", dtype=True, precise_float=False)
        return data_frame

    def _preprocess(self, data):
        logger.info("Do no pre-processing by default")
        return data

    def _inference(self, data):
        inference_result = predict(self.model, data)
        return inference_result

    def _postprocess(self, data):
        logger.info("Process inference result")
        result = predictions_to_jsonable(data)
        return result


def load_model(model_path):
    try:
        logger.info("Try to load sklearn model...")
        load_model = joblib.load(model_path)
    except:
        try:
            logger.info("Try to load xgboost model...")
            load_model = xgb.Booster(model_file=model_path)
        except:
            logger.error("Model type is not supported!")
            logger.error(traceback.format_exc())
            raise
    return load_model


def predict(model, data):
    try:
        pre_result = model.predict(data.values)
        pre_result = pre_result.tolist()
        return pre_result
    except:
        try:
            pre_data = xgb.DMatrix(data.values)
            pre_result = model.predict(pre_data)
            pre_result = pre_result.tolist()
        except:
            logger.error('Predict failed!')
            logger.error(traceback.format_exc())
            raise
    return pre_result
