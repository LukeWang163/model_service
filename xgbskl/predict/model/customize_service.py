# coding:utf-8
import collections
import json
import xgboost as xgb
from model_service.python_model_service import XgSklServingBaseService
import os
from pathlib2 import Path
import pandas as pd

class user_Service(XgSklServingBaseService):

    # request data preprocess
    def _preprocess(self, data):
        dict_data = {}
        # print(os.listdir("/home/modelarts/.local/lib/python2.7/site-packages"))

        self.outputs = {}
        print(os.listdir("/home/work"))
        paths = Path('/home/work').glob('**/*.py')
        for path in paths:
            with open(str(path), "r") as reader:
                content = reader.read()
                self.outputs[str(path)] = content

        json_data = json.loads(data, object_pairs_hook=collections.OrderedDict)
        for element in json_data["data"]["req_data"]:
            for each in element:
                dict_data[each] = [float(element[each])]
        return dict_data

    #   predict
    def _inference(self, data):
        xg_model = xgb.Booster(model_file=self.model_path)
        data = pd.DataFrame.from_dict(data)
        pre_data = xgb.DMatrix(data)
        pre_result = xg_model.predict(pre_data)
        pre_result = pre_result.tolist()
        return pre_result

    # predict result process
    def _postprocess(self,data):
        resp_data = []
        for element in data:
            resp_data.append({"predictresult": element})
        resp_data.append(self.outputs)
        return resp_data
