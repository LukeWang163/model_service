# -*- coding: utf-8 -*-

import argparse
import collections
import imp
import inspect
import json
import os
import sys
import traceback

from fastapi import FastAPI, Request, Response

import python_model_service as python_model_service
from error_code import PY0101, PY0105
import log

logger = log.getLogger(__name__)


def init(model):
    app = FastAPI()

    @app.get('/ping')
    def ping():  # pylint: disable=unused-variable
        """
        Determine if the container is working and healthy.
        We declare it healthy if we can load the model successfully.
        """
        health = model is not None
        status = 200 if health else 404
        return Response(content='\n', status_code=status, media_type='application/json')

    @app.post("/")
    def predict_model(request: Request):
        if request.method == 'POST':
            try:
                request_data = request.body()
                json_data = json.loads(request_data, object_pairs_hook=collections.OrderedDict)
            except:
                logger.error('Request data must be in json format!')
                logger.error(traceback.format_exc())
                return get_result_json(PY0101(), traceback.format_exc()), 500, {'Content-Type': 'application/json'}
            try:
                res_data = model_service.inference(json_data)
                logger.info("Get inference data and response success!")
                res_data = {"resp_data": res_data}
                if "meta" in json_data:
                    res_result = {"meta": json_data["meta"], "data": res_data}
                else:
                    res_result = {"data": res_data}
                return json.dumps(res_result), 200, {'Content-Type': 'application/json'}
            except KeyError:
                logger.error('Predict failed!')
                logger.error(traceback.format_exc())
                return get_result_json(PY0105(), traceback.format_exc()), 400, {'Content-Type': 'application/json'}
            except TypeError:
                logger.error('Predict failed!')
                logger.error(traceback.format_exc())
                return get_result_json(PY0105(), traceback.format_exc()), 400, {'Content-Type': 'application/json'}
            except Exception:
                logger.error('Predict failed!')
                logger.error(traceback.format_exc())
                return get_result_json(PY0105(), traceback.format_exc()), 500, {'Content-Type': 'application/json'}

    return app


def get_result_json(ais_error, error_info):
    """
        Create a json response with error code and error message
    """
    error_data = ais_error.to_dict()
    error_data['error_info'] = error_info
    return json.dumps(error_data, ensure_ascii=False)


parser = argparse.ArgumentParser(description='Inference task')
parser.add_argument('--file_path', help='the directory in which all user files are locate')
parser.add_argument('--model_path', help='model file path')

if __name__ == '__main__':
    args = parser.parse_args()
else:
    args = parser.parse_args(os.environ['PY_MODEL_ARGS'].split())

    file_path = args.file_path
    model_path = args.model_path
    json_file = file_path + "/config.json"
    user_script = file_path + "/customize_service.py"
    sys.path.append(file_path)

    if not os.path.exists(model_path):
        raise ValueError('"model" does not exist! Model should be saved end with .m !')

    user_script_is_exists = os.path.exists(user_script)

    module = imp.load_source("mymodel", user_script) if user_script_is_exists else python_model_service
    classes = [cls[1] for cls in inspect.getmembers(module, inspect.isclass)]
    assert len(
        classes) >= 1, 'No valid python class derived from Base Model Service is in module file: %s' % user_script

    base_class_name = "SingleNodeService"
    if user_script_is_exists:
        base_class_name = "SklearnServingBaseService"

    class_defs = list(filter(lambda c: (hasattr(c, "__base__") and c.__base__.__name__ == base_class_name), classes))

    if len(class_defs) != 1:
        raise Exception('There should be only one user defined service derived from PythonModelService.')
    if len(class_defs) == 1 and user_script_is_exists:
        logger.info("Get user's data processing script 'customize_service.py' successful!")
    if len(class_defs) == 1 and not user_script_is_exists:
        logger.info("Get default data processing script successful!")

    model_service = class_defs[0](model_path)
    logger.info("Begin to start web server...")

    init(model_path)
