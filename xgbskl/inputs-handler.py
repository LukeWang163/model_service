from __future__ import print_function
import os
import json
import subprocess
import sys
import uuid
import moxing as mox

MA_ENV_PREFIX = 'MA_'

ENV_INPUTS = MA_ENV_PREFIX + 'INPUTS'

MA_MODELARTS_DIR = '/home/work/modelarts'
MA_INPUTS_DIR = '/home/work/modelarts/inputs'
MA_MODELARTS_DOWNLOADER = '/home/work/modelarts-downloader.py'

ENV_CACHE_HOME = 'CACHE_HOME'

MA_INPUTS_FIELD = 'inputs'
MA_INPUTS_NAME_FIELD = 'name'
MA_INPUTS_PARAMETER_FILED = 'parameter'
MA_INPUTS_VALUE_FILED = 'value'
MA_INPUTS_DATA_SOURCE_FILED = 'data_source'
MA_INPUTS_DATASET_FILED = 'dataset'
MA_INPUTS_OBS_FILED = 'obs'
MA_INPUTS_OBS_URL_FILED = 'obs_url'

MA_LOG_PREFIX = '[ModelArts Service Log]'


def base_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def log(text):
    base_print(MA_LOG_PREFIX + 'INFO: %s' % text)


def warn(text):
    base_print(MA_LOG_PREFIX + 'WARN: %s' % text)


def err(text):
    base_print(MA_LOG_PREFIX + 'ERROR: %s' % text)


# call modelarts-downloader.py to handle the obs input
def handle_raw_obs_input(raw_obs_url, dest_path):
    download_cmd = 'python %s -s %s -d %s'
    if raw_obs_url.endswith(os.path.sep):
        # recursive download the content of dir (object) and skip creating the dir
        download_cmd += ' --skip-creating-dir -r'

    command = download_cmd % (MA_MODELARTS_DOWNLOADER, raw_obs_url, dest_path)
    return subprocess.Popen(command, shell=True).wait()


# call Moxing api to handle the data set input
def handle_data_set_input(raw_obs_url, dest_path):
    try:
        mox.file.copy_manifest(raw_obs_url, dest_path)
        return 0
    except Exception as e:
        err('moxing copy dataset by manifest file failed: ' + str(e))
        return 255


if __name__ == '__main__':
    if ENV_INPUTS not in os.environ:
        log('env MA_INPUTS is not found, skip the inputs handler')
        exit(0)

    inputs_json_string = os.getenv(ENV_INPUTS)
    if inputs_json_string.strip() == '':
        log('env MA_INPUTS is empty, skip the inputs handler')
        exit(0)

    # make /home/work/modelarts dir
    if not os.path.exists(MA_MODELARTS_DIR):
        os.makedirs(MA_MODELARTS_DIR)

    # test local_ssd env
    enable_local_ssd = ENV_CACHE_HOME in os.environ
    if enable_local_ssd:
        local_ssd_dir = os.getenv(ENV_CACHE_HOME)
        uuid = uuid.uuid4()
        # /cache/inputs-${uuid}
        inputs_in_local_ssd_dir = '%s/%s-%s' % (local_ssd_dir, MA_INPUTS_FIELD, uuid)

        sp = subprocess.Popen('mkdir -p %s' % inputs_in_local_ssd_dir, shell=True)
        return_code = sp.wait()
        if return_code != 0:
            err('make the cache dir [%s] of inputs failed, return code: [%d]' %
                (inputs_in_local_ssd_dir, return_code))
            exit(return_code)

        os.chdir(MA_MODELARTS_DIR)
        if not os.path.exists(MA_INPUTS_FIELD):
            # link /home/work/modelarts/inputs to /cache/inputs-${uuid}
            sp = subprocess.Popen('ln -s %s %s' % (inputs_in_local_ssd_dir, MA_INPUTS_FIELD),
                                  shell=True)
            return_code = sp.wait()
            if return_code != 0:
                err('link the input dir [%s/%s] to cache dir failed, return code: [%d]' %
                    (MA_MODELARTS_DIR, MA_INPUTS_FIELD, return_code))
                exit(return_code)
        else:
            warn('inputs file exists')

    '''
    {
          "inputs": [
            {
              "name": "code",
          "description": "training code",
          "parameter": {
                "label": "code_dir",
            "value": "my-code"
          },
          "data_source": {
                "obs": {
                  "obs_url": "s3://x/x/" ---> dir (object)
            }
          }
        },
        {
              "name": "checkpoint",
          "description": "ckpt",
          "parameter": {
                "label": "ckpt",
            "value": "my-ckpt"
          },
          "data_source": {
                "obs": {
                  "obs_url": "s3://test-wpy/zl/V010.ckpt" ---> file
            }
          }
        },
        {
              "name": "data set",
          "description": "data set",
          "parameter": {
                "label": "data_dir",
            "value": "my-data"
          },
          "data_source": {
                "dataset": {
                  "dataset_id": "YYY",
              "dataset_version": "XXX",
              "obs_url": "s3://test-wpy/zl/V020.manifest" ---> manifest
            }
          }
        }
      ]
    }
    '''
    inputs_json = json.loads(inputs_json_string)
    inputs = inputs_json[MA_INPUTS_FIELD]

    for each_input in inputs:
        input_suffix_dir_name = each_input[MA_INPUTS_PARAMETER_FILED][MA_INPUTS_VALUE_FILED]
        obs_url = ''

        data_source_json = each_input[MA_INPUTS_DATA_SOURCE_FILED]
        data_source_type = 'unknown'
        if MA_INPUTS_DATASET_FILED in data_source_json:
            data_source_type = MA_INPUTS_DATASET_FILED
            obs_url = data_source_json[MA_INPUTS_DATASET_FILED][MA_INPUTS_OBS_URL_FILED]
        elif MA_INPUTS_OBS_FILED in data_source_json:
            data_source_type = MA_INPUTS_OBS_FILED
            obs_url = data_source_json[MA_INPUTS_OBS_FILED][MA_INPUTS_OBS_URL_FILED]
        else:
            err('unknown %s' % MA_INPUTS_DATA_SOURCE_FILED)
            exit(1)

        raw_input_name = each_input[MA_INPUTS_NAME_FIELD]
        input_name = '--'
        try:
            input_name = mox.framework.util.compat.as_str(raw_input_name)
        except TypeError:
            warn('the name of the input can not be decoded, it will show as --')

        log('download the content of [%s] inputs' % input_name)

        input_full_dir = os.path.join(MA_INPUTS_DIR, input_suffix_dir_name)
        input_local_dir = os.path.abspath(input_full_dir)
        if not os.path.exists(input_local_dir):
            os.makedirs(input_local_dir)

        os.chdir(input_local_dir)

        return_code = 0
        if data_source_type == MA_INPUTS_OBS_FILED:
            return_code = handle_raw_obs_input(obs_url, './')
        else:
            return_code = handle_data_set_input(obs_url, input_local_dir)

        if return_code != 0:
            # split the log output into two line as input_name is a unicode string
            err('download the content of [%s] inputs failed' % input_name)
            err('return code: [%d]' % return_code)
            exit(return_code)

        log('download the content of [%s] inputs successfully' % input_name)
        log('it can be accessed at local dir [%s]' % input_local_dir)

    exit(0)
