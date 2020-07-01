# -*- coding: utf-8 -*-
import collections
import json
import traceback

import xgboost as xgb
from sklearn.externals import joblib

from . import log
from .model_service import SingleNodeService

logger = log.getLogger(__name__)


class XgSklServingBaseService(SingleNodeService):

    def __init__(self, model_path):
        self.model_path = model_path

    def _preprocess(self, data):
        logger.info("Begin to handle data from user data...")
        list_data = []
        json_data = json.loads(data, object_pairs_hook=collections.OrderedDict)
        for element in json_data["data"]["req_data"]:
            array = []
            for each in element:
                array.append(element[each])
            list_data.append(array)
        return list_data

    def _inference(self, pre_data):
        pre_result = predict(self.model_path, pre_data)
        return pre_result

    def _postprocess(self, pre_data):
        logger.info("Get new data to respond...")
        resp_data = []
        for element in pre_data:
            resp_data.append({"predictresult": element})
        return resp_data


def predict(model_path, pre_data):

    try:
        logger.info("Begin to load sklearn model...")
        load_model = joblib.load(model_path)
    except:
        try:
            logger.info("Begin to load xgboost model...")
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
