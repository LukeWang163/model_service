#!/usr/bin/env python

"""
Description: script for python-job-runner
"""

import os
import sys
import argparse
import traceback
import json

batch_parameter = ''
for paramter in sys.argv[1:]:
    if 'obs://' in paramter:
        paramter = paramter.replace('obs://', 's3://')
    if '--app-url' in paramter:
        paramter = paramter.replace('--app-url', '--app_url')
    if '--data-url' in paramter:
        paramter = paramter.replace('--data-url', '--data_url')
    if '--boot-file' in paramter:
        paramter = paramter.replace('--boot-file', '--boot_file')
    if '--log-file' in paramter:
        paramter = paramter.replace('--log-file', '--log_file')
    if '--train-url' in paramter:
        paramter = paramter.replace('--train-url', '--train_url')
    batch_parameter = batch_parameter + ' ' + paramter
os.environ['batch_parameter'] = batch_parameter

script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_root + '/../pylib')

DEFAULT_LOG_DIR = script_root + '/../log'
LOG_DIR = os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
LOG_FILE = LOG_DIR + '/script_python.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
OBS_CONF = script_root + '/../conf/obs.conf'
SCRIPT_CONF = script_root + '/../conf/script-info.conf'
LOG_CONF = script_root + '/../conf/log.conf'

import return_code as code
import systraceutils as lg

LOGGER = lg.getLogger("start", LOG_FILE, maxfilesize=20, maxbackupcount=10, level=LOG_LEVEL)


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


def print_title(title=""):
    logit("INFO", "=" * 15 + " %s " % title + "=" * 15)


def get_original_obs_data_url():
    input_json = os.getenv("MA_INPUTS")
    data_url = ""

    if json.loads(input_json).get("inputs")[0].get("data_source").__contains__("dataset"):
        data_url = json.loads(input_json).get("inputs")[0].get("data_source").get("dataset").get("obs_url")
    elif json.loads(input_json).get("inputs")[0].get("data_source").__contains__("obs"):
        data_url = json.loads(input_json).get("inputs")[0].get("data_source").get("obs").get("obs_url")
    else:
        pass

    return data_url


def get_original_obs_train_url():
    output_json = os.getenv("MA_OUTPUTS")
    train_url = json.loads(output_json).get("outputs")[0].get("data_source").get("obs").get("obs_url") \
        if output_json is not None else ""
    return train_url


class Config(object):
    """docstring for Config"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Process some integers.')
        self.parser.add_argument('--app-url', help='app path in obs')
        self.parser.add_argument('--data_url', help='data path in obs')
        self.parser.add_argument('--boot-file', help='boot file path in obs')
        self.parser.add_argument('--log-file', help='local log file (in container)')
        self.parser.add_argument('--train_url', help='model path in obs')

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

    def update_obsaksk(self, config_path, new_config):

        print_title("update obsaksk")
        obs_config = self.get_json(config_path)
        if not obs_config:
            logit("error", "obs config is empty")
            return code.ERROR
        else:
            for key in new_config:
                obs_config.update({key: new_config[key]})

            json.dump(obs_config, open(config_path, 'w'))
        return code.NORMAL

    def update_script(self, config_path, new_config):

        print_title("update script")
        script_config = self.get_json(config_path)
        if not script_config:
            logit("error", "script config is empty")
            return code.ERROR
        else:
            for key in new_config:
                script_config.update({key: new_config[key]})
            logit("info", script_config)
            json.dump(script_config, open(config_path, 'w'))
        return code.NORMAL

    def update_logconf(self, config_path, new_config):

        print_title("update log")
        content = ""
        for line in open(config_path, 'r').readlines():
            if 'LogFileDir' in line:
                line = 'LogFileDir = %s\
' % new_config.get('LogFileDir', '../log')
            elif 'LogFileName' in line:
                line = 'LogFileName = %s\
' % new_config.get('LogFileName', 'obs_python.log')
            content += line
        flog = open(config_path, 'w')
        flog.write(content)
        flog.close()
        return code.NORMAL

    def init_from_env(self):

        OBS_AK = os.getenv("AWS_ACCESS_KEY_ID", "")
        OBS_SK = "fakeSK"
        OBS_SERVER = os.getenv("S3_ENDPOINT", "")

        if all((OBS_AK, OBS_SK, OBS_SERVER)):
            self.update_obsaksk(OBS_CONF, {
                "OBS_AK": OBS_AK,
                "OBS_SK": OBS_SK,
                "OBS_SERVER": OBS_SERVER
            })
        else:
            logit("error", 'invalid ak/sk/obsserver')

    def remove_obs_prefix(self, obs_path):
        if obs_path.startswith("obs://"):
            return obs_path.split("obs://")[1]
        elif obs_path.startswith("s3://"):
            return obs_path.split("s3://")[1]

        return obs_path

    def init_from_cmd(self):
        try:

            ARGS = self.parser.parse_known_args()
            ARGS = ARGS[0]

            if ARGS.app_url:
                app_url = self.remove_obs_prefix(ARGS.app_url)
                self.update_obsaksk(OBS_CONF, {"OBS_BUCKET": app_url.split('/')[0]})
                os.environ['APP_URL'] = app_url if app_url.endswith("/") else app_url + "/"

            if ARGS.data_url:
                if use_algorithm:
                    os.environ['USER_DEFINED_INPUT_PATH'] = ARGS.data_url
                    os.system('mkdir -p %s' % ARGS.data_url)
                    original_data_url = get_original_obs_data_url()
                    self.update_obsaksk(OBS_CONF, {
                        "OBS_BUCKET_DATA": self.remove_obs_prefix(original_data_url)
                    })
                    data_url = self.remove_obs_prefix(original_data_url)
                    os.environ['DATA_URL'] = data_url[:-1] if data_url.endswith("/") else data_url
                else:
                    self.update_obsaksk(OBS_CONF, {
                        "OBS_BUCKET_DATA": self.remove_obs_prefix(ARGS.data_url)
                    })
                    DATA_URL = self.remove_obs_prefix(ARGS.data_url)
                    os.environ['DATA_URL'] = DATA_URL

            if ARGS.boot_file:
                self.update_script(SCRIPT_CONF, {
                    "app_dir_obs": self.remove_obs_prefix(ARGS.app_url).split('/', 1)[1],
                    "app_dir_local": '/tmp/' + os.path.basename(ARGS.app_url),
                    "boot_file_path_local": '/tmp/' + (ARGS.boot_file.split('/', 1)[1])})

                if ARGS.log_file:
                    LOG_PATH_LOCAL = ARGS.log_file
                    LogFileDir = os.path.dirname(LOG_PATH_LOCAL)
                    LogFileName = os.path.basename(LOG_PATH_LOCAL)
                    self.update_logconf(LOG_CONF, {
                        "LogFileDir": os.path.dirname(LOG_PATH_LOCAL),
                        "LogFileName": os.path.basename(LOG_PATH_LOCAL)
                    }
                                        )

                    if ARGS.train_url:
                        if use_algorithm:
                            os.environ['USER_DEFINED_OUTPUT_PATH'] = ARGS.train_url
                            os.system('mkdir -p %s' % ARGS.train_url)
                            original_train_url = get_original_obs_train_url()
                            train_url = self.remove_obs_prefix(original_train_url)
                            os.environ['TRAIN_URL'] = train_url[1:-1] if train_url.endswith("/") else train_url[1:]
                        else:
                            TRAIN_URL = self.remove_obs_prefix(ARGS.train_url)
                            os.environ['TRAIN_URL'] = TRAIN_URL

        except Exception:
            logit("error", traceback.format_exc())
            sys.exit(code.OPERATION_FAIL)

        def init_para(self):
            """
            get parameters from cmd and dump into conf/*.conf
            """
            self.init_from_env()
            self.init_from_cmd()


if __name__ == '__main__':

    logit("info", "args: %s" % str(sys.argv))
    use_algorithm = True if os.getenv('MA_ALGORITHM_CODE_SIZE') is not None else False
    config = Config()
    config.init_para()

    import runner

    op = runner.Runner()
    op.download_script_by_tree() if use_algorithm else op.download_script()
    op.pip_install_requirement()
    result = op.start_script()

    print("\[Modelarts Service Log]Training completed.")
    if result == 0:
        op.sync_local2obs(use_algorithm)
        sys.exit(0)
    else:
        sys.exit(1)
