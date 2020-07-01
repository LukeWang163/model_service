#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import traceback
from obs.client import ObsClient
from obs.model import PutObjectHeader
from obs.model import SseKmsHeader, SseCHeader
from obs.model import GetObjectRequest
from obs.model import GetObjectHeader
from obs.model import ObjectStream
from obs.ilog import *

os.environ['S3_ACCESS_KEY_ID'] = os.getenv("AWS_ACCESS_KEY_ID", "")
os.environ['S3_ENDPOINT'] = os.getenv("S3_ENDPOINT", "")
os.environ['S3_SECRET_ACCESS_KEY'] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
os.environ['MINER_USER_ACCESS_KEY'] = os.getenv("AWS_ACCESS_KEY_ID", "")
os.environ['MINER_OBS_URL'] = os.getenv("S3_ENDPOINT", "")
os.environ['MINER_USER_SECRET_ACCESS_KEY'] = os.getenv("AWS_SECRET_ACCESS_KEY", "")

import moxing as mox

script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_root + '/../pylib')

import return_code as code

DEFAULT_LOG_DIR = script_root + '/../log'
LOG_DIR = os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
LOG_FILE = LOG_DIR + '/script_python.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_CONF = script_root + '/../conf/log.conf'

import systraceutils as lg

LOGGER = lg.getLogger("python_job_runner", LOG_FILE, maxfilesize=20, maxbackupcount=10, \ \
    level = LOG_LEVEL)

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


class ObsUtils(object):
    """docstring for ObsUtils"""

    def __init__(self):
        self.OBS_AK = ""
        self.OBS_SK = ""
        self.OBS_SERVER = ""
        self.OBS_BUCKET = ""
        self.OBS_DATASET_DIR = ""
        self.OBS_MODEL_DIR = ""
        self.TRAIN_DATASET = ""
        self.MODEL_NAME = ""
        self.LOCAL_WORK_DIR = ""
        self.obsClient = None

    def initLog(self, log_conf="./log.conf"):
        """
        函数功能：初始化日志
        函数原型：LogInit(logCog=LogConf())
        参数说明：logCog:日志配置文件信息,
        LogConf(confFile=None,sec=None),confFile:配置文件路径,sec：配置文件命名空间
        引入库: from com.obs.log.Log import *
        """
        print(log_conf)
        self.obsClient.initLog(LogConf(log_conf), 'obs_utils')  # 初始化obsclient日志
        LogClient(LogConf(log_conf))  # 初始化global日志

    def setupObs(self, obs_config):

        if isinstance(obs_config, dict):
            self.OBS_AK = str(obs_config.get("OBS_AK", ""))
            self.OBS_SK = str(obs_config.get("OBS_SK", ""))
            self.OBS_SERVER = str(obs_config.get("OBS_SERVER", ""))
            self.OBS_BUCKET = str(obs_config.get("OBS_BUCKET", ""))
            self.OBS_DATASET_DIR = str(obs_config.get("OBS_DATASET_DIR", ""))
            self.OBS_MODEL_DIR = str(obs_config.get("OBS_MODEL_DIR", ""))
            self.TRAIN_DATASET = str(obs_config.get("TRAIN_DATASET", ""))
            self.MODEL_NAME = str(obs_config.get("MODEL_NAME", ""))
            self.LOCAL_WORK_DIR = str(obs_config.get("LOCAL_WORK_DIR", ""))

            self.getObsClient()

        else:
            logit("error", "obs_config is empty")
            return code.OPERATION_FAIL

        return code.NORMAL

    def getObsClient(self):
        self.obsClient = ObsClient(
            access_key_id=self.OBS_AK,
            secret_access_key=self.OBS_SK,
            server=self.OBS_SERVER
        )

        self.initLog(LOG_CONF)

    def downloadDataset(self):
        print_title("Start to download dataset from OBS")
        obsClient = getObsClient()
        try:
            resp = obsClient.getObject(self.OBS_BUCKET,
                                       self.OBS_DATASET_DIR + self.TRAIN_DATASET,
                                       downloadPath=os.path.join(self.LOCAL_WORK_DIR, self.TRAIN_DATASET))
            if resp.status < 300:
                logit("info", 'Succeeded to download training dataset')
            else:
                logit("info", 'Failed to download ' + self.TRAIN_DATASET)
                logit("info", 'errorCode:', resp.errorCode)
                logit("info", 'errorMessage:', resp.errorMessage)
                raise Exception('failed to download dataset from OBS')
        finally:
            obsClient.close()

    def PutObject(self, objectKey=""):
        sseHeader = SseKmsHeader.getInstance()  # 设置SSE-KMS加密
        Lheaders = PutObjectHeader(md5=None, acl='public-read-write', location=None,
                                   contentType='text/plain', sseHeader=sseHeader)
        Lmetadata = {'key': 'value'}

        resp = self.obsClient.putObject(bucketName=self.OBS_BUCKET, objectKey=objectKey,
                                        content='msg content to put', metadata=Lmetadata, headers=Lheaders)

        print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:',
              resp.errorMessage)
        print(resp.header)

    def downloadObject(self, objectKey="", downloadPath="./"):
        print_title("Start to download object from OBS")
        resp = self.obsClient.getObject(bucketName=self.OBS_BUCKET,
                                        objectKey=objectKey, downloadPath=downloadPath)
        if resp.status < 300:
            logit("info", 'Succeeded to download training dataset')
        else:
            logit("info", 'Failed to download ' + self.TRAIN_DATASET)
            logit("info", 'errorCode:', resp.errorCode)
            logit("info", 'errorMessage:', resp.errorMessage)
            raise Exception('failed to download dataset from OBS')

    def downloadFolder(self, obs_path="", local_path="./"):
        s3_path = "s3://" + self.OBS_BUCKET + "/" + obs_path
        local_dir = os.path.dirname(local_path)
        mox.file.copy_parallel(s3_path, local_dir)
