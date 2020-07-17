# -*- coding: utf-8 -*-
import argparse
import collections
import inspect
import json
import os
import sys
import traceback
import uvicorn
from fastapi import FastAPI, Request, Response
import pandas as pd
import base64
from json import JSONEncoder
import numpy as np
from model_service import *
import python_model_service as python_model_service
from error_code import PY0101, PY0105
import log
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

logger = log.getLogger(__name__)
app = FastAPI()


@app.get('/ping')
def ping():  # pylint: disable=unused-variable
    """
    Determine if the container is working and healthy.
    We declare it healthy if we can load the model successfully.
    """
    # health = model is not None
    # status = 200 if health else 404
    return Response(content='ok', status_code=200, media_type='application/json')


@app.post("/")
async def predict_model(request: Request):
    if request.method == 'POST':
        try:
            request_data = await request.body()
            #json_data = json.loads(request_data, object_pairs_hook=collections.OrderedDict)
            # df = pd.read_json(request_data, orient="split")
            # print(df)
        except:
            logger.error('Request data must be in json format!')
            logger.error(traceback.format_exc())
            return get_result_json(PY0101(), traceback.format_exc()), 500, {'Content-Type': 'application/json'}
        try:
            # model_service = python_model_service.SklearnServingBaseService("/Users/petra/Workspace/mnist/xgboost.m")
            model_service = python_model_service.SklearnServingBaseService("E:\\KDD99\\xgboost.m")
            res_data = model_service.inference(request_data)
            # try:
            #     json.loads(res_data)
            # except ValueError:
            #     res_data = predictions_to_json(res_data)
            logger.info("Get inference data and response success!")
            result = {"result": res_data, "success": True, "errorLog": ""}
            return Response(content=json.dumps(result, cls=NumpyEncoder),
                            status_code=200,
                            media_type='application/json')
        except KeyError:
            logger.error('Predict failed!')
            logger.error(traceback.format_exc())
            return Response(content=get_result_json(PY0105(), traceback.format_exc()),
                            status_code=400,
                            media_type='application/json')
        except TypeError:
            logger.error('Predict failed!')
            logger.error(traceback.format_exc())
            return Response(content=get_result_json(PY0105(), traceback.format_exc()),
                            status_code=400,
                            media_type='application/json')
        except Exception:
            logger.error('Predict failed!')
            logger.error(traceback.format_exc())
            return Response(get_result_json(PY0105(), traceback.format_exc()),
                            status_code=500,
                            media_type='application/json')

def get_result_json(ais_error, error_info):
    """
        Create a json response with error code and error message
    """
    error_data = ais_error.to_dict()
    error_data['success'] = False
    error_data['result'] = ''
    error_data['errorLog'] = error_info
    return json.dumps(error_data, ensure_ascii=False)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
