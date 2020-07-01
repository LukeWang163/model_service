# -*- coding: utf-8 -*-
"""
DL webservice app
"""
import inspect
import io
import json
import os
import tempfile
import traceback
from flask import Flask, request
from tf import log

app = Flask("aa")
from tf.error_code import MR0101, MR0105

LOGGER = log.getLogger(__name__)
import argparse
import collections


def get_result_json(ais_error):
    """
        Create a json response with error code and error message
    """
    data = ais_error.to_dict()
    data['words_result'] = {}

    return json.dumps(data, ensure_ascii=False)


@app.route('/health', methods=['GET'])
def healthy():
    return "{\"status\": \"OK\"}"


@app.route('/', methods=['POST'])
def inference_task():
    # get all data from different media
    rec_dict = {}
    if request.json:
        rec_dict = request.json
    elif request.form or request.files:
        form = request.form
        files = request.files
        rec_dict = {}
        for k, v in form.items():
            rec_dict[k] = v

        for k, file in files.items():
            list = files.getlist(k)
            filename_dict = collections.OrderedDict()
            for one in list:
                if isinstance(one.stream, tempfile.SpooledTemporaryFile):
                    filename_dict[one.filename] = io.BytesIO(one.stream.read())
                elif isinstance(one.stream, io.BytesIO):
                    filename_dict[one.filename] = one.stream
                else:
                    LOGGER.error('receive file not recognized!')
                    raise Exception

            rec_dict[k] = filename_dict
    else:
        return get_result_json(MR0101()), 400, {'Content-Type': 'application/json'}

    args = request.args
    for k, v in args.items():
        rec_dict[k] = v

    try:
        res = model_service.inference(rec_dict)
        return json.dumps(res, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
    except KeyError as k:
        LOGGER.error('Algorithm crashed!')
        LOGGER.error(traceback.format_exc())
        return get_result_json(MR0105()), 400, {'Content-Type': 'application/json'}
    except TypeError as te:
        LOGGER.error('Algorithm crashed!')
        LOGGER.error(traceback.format_exc())
        return get_result_json(MR0105()), 400, {'Content-Type': 'application/json'}
    except Exception as e:
        LOGGER.error('Algorithm crashed!')
        LOGGER.error(traceback.format_exc())
        return get_result_json(MR0105()), 500, {'Content-Type': 'application/json'}


parser = argparse.ArgumentParser(description='Flask App')
parser.add_argument('--model_path', action="store", default="/home/mind/model/1", type=str)
parser.add_argument('--model_name', action="store", default="serve", type=str)
parser.add_argument('--tf_server_name', action="store", default="127.0.0.1", type=str)
parser.add_argument('--service_file', action="store", type=str)

if __name__ == "__main__":

    args = parser.parse_args()
else:
    args = parser.parse_args(os.environ['TF_MODEL_ARGS'].split())

LOGGER.info("args: %s", args)

from tf.model_service import load_service
from tf import model_service as tfserving_vision_service, settings
from tf.model_service.tfserving_model_service import TfServingBaseService

model_path = args.model_path
model_name = args.model_name
model_service_file = args.service_file

tf_server_name = args.tf_server_name

module = load_service(model_service_file) if model_service_file else tfserving_vision_service
classes = [cls[1] for cls in inspect.getmembers(module, inspect.isclass)]

assert len(classes) >= 1, 'No valid python class derived from Base Model Service is in module file: %s' % model_service_file

class_defs = list(filter(lambda c: issubclass(c, TfServingBaseService) and len(c.__subclasses__()) == 0, classes))

if len(class_defs) != 1:
    raise Exception('There should be one user defined service derived from ModelService.')

model_service = class_defs[0](model_name, model_path)


settings.DEFAULT_TF_SERVER_NAME = tf_server_name

