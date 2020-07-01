import os
import json
from obs import ObsClient
from collections import OrderedDict
import collections

LOCAL_MODEL_DIR = '/tmp/'
LOCAL_CONFIG_DIR = '/tmp/config.json'
AK = os.getenv('AWS_ACCESS_KEY_ID')
SK = os.getenv('AWS_SECRET_ACCESS_KEY')
obs_endpoint = os.getenv('S3_ENDPOINT')
data_path = os.getenv('DATA_URL')
obs_path = os.getenv('TRAIN_URL')

if AK is None:
    AK = ''
    print('AK is null')

if SK is None:
    SK = ''
    print('SK is null')

if obs_endpoint is None:
    obs_endpoint = ''
    print('obs_endpoint is null')
print("obs_endpoint: " + str(obs_endpoint))

if data_path is None:
    data_path = ''
    print('data_path is null')
print("data_path: " + str(data_path))

if obs_path is None:
    obs_path = ''
    print('obs_path is null')
print("obs_path: " + str(obs_path))


def create_model_dir():
    obsClient = ObsClient(AK, SK, is_secure=True, server=obs_endpoint)
    bucketName = obs_path.split("/", 1)[0]
    workDir = obs_path.split("/", 1)[1] + '/model/'
    resp_dir = obsClient.putContent(bucketName, workDir, content=None)

    if resp_dir.status < 300:
        print('Create workDir model success:', resp_dir.requestId)
        return workDir

    print('Fail to create workDir model and errorCode:', resp_dir.errorCode)
    print('errorMessage:', resp_dir.errorMessage)
    return ""


model_path = create_model_dir()


def upload_obs(local_path, file_name):
    obsClient = ObsClient(AK, SK, is_secure=True, server=obs_endpoint)
    filemodel = model_path + file_name
    bucketName = obs_path.split("/", 1)[0]
    resp = obsClient.putFile(bucketName, filemodel, file_path=local_path)
    print(resp)
    return 0


def download_obs(local_path, obs_path):
    TestObs = ObsClient(AK, SK, is_secure=True, server=obs_endpoint)
    bucketName = obs_path.split("/", 1)[0]
    resultFileName = obs_path.split("/", 1)[1]

    resp = TestObs.getObject(bucketName, resultFileName, downloadPath=local_path)
    if resp.status < 300:
        print('Succeeded to download training dataset')
    else:
        print('Failed to download ')


def download_data(data_file_name):
    local_data_file_path = os.path.join(LOCAL_MODEL_DIR, data_file_name)
    obs_path = data_path + '/' + data_file_name
    download_obs(local_data_file_path, obs_path)
    return local_data_file_path


def upload_model(model_engine, model, model_name, sc=None):
    model_engine = model_engine.upper()
    model_path = os.path.join(LOCAL_MODEL_DIR, model_name)
    if model_engine == 'XGBOOST':
        model.save_model(model_path)
    elif model_engine == 'SCIKIT_LEARN':
        from sklearn.externals import joblib
        joblib.dump(model, model_path)
    elif model_engine == 'SPARK_MLLIB':
        model.save(sc, model_path)
    else:
        print('model_engine:' + model_engine + 'not exit')
    upload_obs(model_path, model_name)


def create_config(model_engine, input_type_list, output_type, metrics_value):
    schema_model = json.loads(
            '{\"model_algorithm\":\"gbtree_classification\",\"model_type\":\"XGBoost\",\"metrics\":{},'
        '\"apis\":[{\"protocol\":\"http\",\"url\":\"/\",\"method\":\"post\",\"request\":{\"Content-type\":\"applicaton/json\",'
        '\"data\":{\"type\":\"object\",\"properties\":{\"data\":{\"type\":\"object\",\"properties\":{\"req_data\":{\"type\":\"array\",'
        '\"items\":[{\"type\":\"object\",\"properties\":{}}]}}}}}},\"response\":{\"Content-type\":\"applicaton/json\",'
        '\"data\":{\"type\":\"object\",\"properties\":{\"resp_data\":{\"type\":\"array\",'
        '\"items\":[{\"type\":\"object\",\"properties\":{\"predictresult\":{}}}]}}}}}]}',
        object_pairs_hook=OrderedDict)
    input_properties = collections.OrderedDict()
    input_num = len(input_type_list)
    for i in range(input_num):
        index = "input_%s" % (i + 1)
        input_properties[index] = {"type": input_type_list[i]}
    output_properties = {"predictresult": output_type}
    schema_model['model_type'] = model_engine
    schema_model['metrics'] = metrics_value
    schema_model["apis"][0]["request"]["data"]["properties"]["data"]["properties"]["req_data"]["items"][0][
            "properties"] = input_properties
    schema_model["apis"][0]["response"]["data"]["properties"]["resp_data"]["items"][0]["properties"] = output_properties
    with open(LOCAL_CONFIG_DIR, 'w') as f:
        json.dump(schema_model, f)
    upload_obs(LOCAL_CONFIG_DIR, "config.json")

