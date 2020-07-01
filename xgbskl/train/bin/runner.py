"""
Description: script for python-job-runner
"""

import sys
import os
import traceback
import json
from subprocess import Popen, PIPE, STDOUT

script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_root + '/../pylib')

import return_code as code
from obs_utils import ObsUtils

DEFAULT_LOG_DIR = script_root + '/../log'
LOG_DIR = os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
LOG_FILE = LOG_DIR + '/script_python.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
OBS_CONF = script_root + '/../conf/obs.conf'
SCRIPT_CONF = script_root + '/../conf/script-info.conf'

import systraceutils as lg

LOGGER = lg.getLogger("python_job_runner", LOG_FILE, maxfilesize=20, maxbackupcount=10, level=LOG_LEVEL)


def logit(level="INFO", msg="", print_able=True):
    if print_able:
        print(msg)
    if level in ("DEBUG", "debug"):
        LOGGER.debug(msg)
    elif level in ("INFO", "info"):
        LOGGER.info(msg)
    elif level in ("WARN", "warn"):
        LOGGER.warn(msg)
    elif level in ("ERROR", "error"):
        LOGGER.error(msg)
    else:
        error_msg = "log level %s not exists" % level
        print(error_msg)
        LOGGER.error(error_msg)


class Runner(object):
    """docstring for Runner"""

    def __init__(self):
        self.obs_config = {}
        self.script_config = {}

    def download_ak_sk(self):

        return code.NORMAL

    def get_json(self, json_file):
        try:
            if not os.path.exists(json_file):
                logit("error", "Json file: %s not exists" % str(json_file))
                return {}
            else:
                logit("debug", "Json file: %s" % str(json_file))

            config_file = json_file

            f = open(config_file)
            config = json.load(f)
            f.close()
            return config

        except Exception:
            logit("error", traceback.format_exc())
            return {}

    def get_obs_config(self, config_path):

        self.obs_config = self.get_json(config_path)
        self.obs_config["OBS_SK"] = os.getenv("AWS_ACCESS_KEY_ID", "")
        if not self.obs_config:
            logit("error", "obs config is empty")
            return code.ERROR
        return code.NORMAL

    def get_script_config(self, config_path):

        self.script_config = self.get_json(config_path)
        if not self.script_config:
            logit("error", "script config is empty")
            return code.ERROR
        return code.NORMAL

    def download_script(self):
        obs = ObsUtils()
        self.get_obs_config(OBS_CONF)
        self.get_script_config(SCRIPT_CONF)
        obs.setupObs(self.obs_config)
        script_path_obs = str(self.script_config.get("app_dir_obs", ""))
        script_path_local = str(self.script_config.get("app_dir_local", ""))
        obs.downloadFolder(script_path_obs, script_path_local)

        return code.NORMAL

    def download_script_by_tree(self):
        obs_app_url = "s3://" + os.getenv("APP_URL")
        download_cmd = "python /home/work/modelarts-downloader.py -r -s %s -d /home/work/modelarts --type %s" % (
            obs_app_url, "algorithm")
        copy_cmd = "cp -rf /home/work/modelarts/%s/* /tmp" % (os.path.basename(obs_app_url[:-1]))
        result_code = os.system(download_cmd + ";" + copy_cmd)
        return result_code

    def sync_local2obs(self, use_algorithm):
        if use_algorithm:
            user_defined_output_path = os.getenv('USER_DEFINED_OUTPUT_PATH')
            upload_cmd = "python /home/work/modelarts-downloader.py -r -s %s -d %s" % (
                user_defined_output_path, "s3://" + os.getenv('TRAIN_URL'))
            if os.listdir(user_defined_output_path):
                os.system(upload_cmd)
        else:
            pass

    def start_script(self):
        result_code = 1
        self.get_script_config(SCRIPT_CONF)
        script_path_local = str(self.script_config.get("boot_file_path_local", ""))
        if os.path.exists(script_path_local):
            name, ext = os.path.splitext(script_path_local)
            if '.py' == ext:
                popen = Popen('python  %s %s' % (script_path_local, os.environ.get('batch_parameter')), shell=True,
                              stdout=PIPE,
                              stderr=PIPE)
                for msg in popen.communicate():
                    print(msg)
                result_code = popen.returncode
            else:
                logit("error", "the script type [%s] doesn't support, should be '.py'" % ext)
        if result_code == 0:
            return code.NORMAL

        return code.ERROR

    def pip_install_requirement(self):
        if os.path.exists('/tmp/pip-requirements.txt'):
            cmd = 'pip install -r /tmp/pip-requirements.txt'
            code = os.system(cmd)
            logit("info", "pip install pip-requirements.txt return code is: %s" % str(code))
        else:
            logit("info", "pip-requirements.txt file not found.")

    def monitor_script(self):

        return code.NORMAL

    def get_log_script(self):

        return code.NORMAL

    def config_script(self):

        return code.NORMAL
