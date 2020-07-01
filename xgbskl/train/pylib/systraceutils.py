#!/usr/bin/env python

import os
import sys
import re
import time
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

__defaultLoggers = {}


def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except Exception:
        return sys.exc_info()[2].tb_frame.f_back


if hasattr(sys, '_getframe'):
    currentframe = lambda: sys._getframe(2)
if __file__[-4:].lower() in ('.pyc', '.pyo'):
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)


def findCaller():
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    f = currentframe()
    if f is not None:
        f = f.f_back
    rv = ('(unknown file)', 0, '(unknown function)')
    while hasattr(f, 'f_code'):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if filename == _srcfile:
            f = f.f_back
            continue
        rv = (
            co.co_filename, f.f_lineno, co.co_name)
        break

    return rv


def removeFile(path, logger=None):
    if not logger:
        logger = getDefaultLogger()
    try:
        if os.path.isfile(path):
            os.remove(path)
        return 0
    except Exception:
        logger.info('remove file %s catch an exception.', path)
        return 1


def zipCompressFile(srcFile, baseFileName, replaceTimestamp=True, logger=None, mod=288):
    if not logger:
        logger = getDefaultLogger()
    zipfp = None
    try:
        try:
            if replaceTimestamp:
                now = datetime.now()
                timeStr = now.strftime('%Y%m%d%H%M%S') + '%03d' % (now.microsecond / 1000)
                zipFileName = '%s.%s.zip' % (baseFileName, timeStr)
            else:
                zipFileName = '%s.zip' % os.path.basename(srcFile)
            zipFile = os.path.join(os.path.dirname(srcFile), zipFileName)
            zipfp = ZipFile(zipFile, 'w', ZIP_DEFLATED)
            zipfp.write(srcFile, zipFileName[:-4])
            zipfp.close()
            if os.path.exists(zipFile):
                os.chmod(zipFile, mod)
                os.remove(srcFile)
        except Exception:
            logger.exception('zip file %s catch an exception.', srcFile)

    finally:
        if zipfp:
            zipfp.close()

    return


def removeExceededBackupFiles(backupFilePath, baseFileName, maxBackupCount, logger=None):
    if not logger:
        logger = getDefaultLogger()
    try:
        zipFileNameList = []
        fileNameList = os.listdir(backupFilePath)
        for fileName in fileNameList:
            if re.match('%s.\\\\w{17}.zip$' % baseFileName, fileName):
                zipFileNameList.append(fileName)

        zipFileCount = len(zipFileNameList)
        if maxBackupCount >= 0 and zipFileCount > maxBackupCount:
            zipFileNameList.sort()
            while len(zipFileNameList) > maxBackupCount:
                zipFileName = zipFileNameList[0]
                zipFilePath = os.path.join(backupFilePath, zipFileName)
                getDefaultLogger().info('remove backup log file %s.', zipFilePath)
                if 0 == removeFile(zipFilePath):
                    zipFileNameList.remove(zipFileName)
                else:
                    logger.error('remove backup log file %s failed.', zipFilePath)
                    break
                zipFileCount = zipFileCount - 1
                if zipFileCount < 0:
                    logger.info('delete count exceed max file size(%d), break.', zipFileCount)
                    break

    except Exception:
        logger.exception('remove exceeded backup files catch an exception.')


class logReCord(logging.LogRecord):

    def __init__(self, record):
        self._record = record
        self.__dict__.update(record.__dict__)

    def getMessage(self):
        if self.exc_info and getattr(self.exc_info[1], 'filename', ''):
            self.exc_info[1].filename = multiple_replace(self.exc_info[1].filename)
        logmsg = multiple_replace(self._record.getMessage())
        return logmsg


class OSSRotatingFileHandler(RotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0):
        self.filename = filename
        self.maxBytes = maxBytes
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)

    def doRollover(self):
        RotatingFileHandler.doRollover(self)
        try:
            dirPath = os.path.dirname(self.baseFilename)
            baseName = os.path.basename(self.baseFilename)
            fileNameList = os.listdir(dirPath)
            for fileName in fileNameList:
                if not re.match('%s.\\\\w+$' % baseName, fileName):
                    continue
                rollingFilePath = os.path.join(dirPath, fileName)
                zipCompressFile(rollingFilePath, baseName)

            removeExceededBackupFiles(dirPath, baseName, self.backupCount)
        except Exception:
            getDefaultLogger().exception('backup trace catch an exception.')

    def emit(self, record):
        try:
            logrecord = logReCord(record)
            sys.tracebacklimit = 1
            RotatingFileHandler.emit(self, logrecord)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def handleError(self, record):
        """
        Handle errors which occur during an emit() call.
        dont't print path to screen
        """
        if sys.stderr:
            ei = sys.exc_info()
            try:
                try:
                    traceback.print_exception(ei[0], ei[1], None, None, sys.stderr)
                    sys.stderr.write('Logged from file %s, line %s\
' % (
                        record.filename, record.lineno))
                except IOError:
                    pass

            finally:
                del ei

        return


redict = {'/tmp': 'BASE_TEMP'}


def multiple_replace(msg):
    rx = re.compile('|'.join(map(re.escape, redict)))
    return rx.sub(lambda match: redict[match.group(0)], msg)


def getTraceLevel():
    level = os.getenv('OSS_PY_TRACE_LEVEL', 'INFO')
    if level == 'DEBUG':
        return logging.DEBUG
    else:
        if level == 'INFO':
            return logging.INFO
        if level == 'WARN':
            return logging.WARN
        if level == 'ERROR':
            return logging.ERROR
        return logging.INFO


def getLogger(module='default', fname='script_python.log', maxfilesize=20, maxbackupcount=10, level="INFO"):
    if not os.path.exists(fname):
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    logger = logging.getLogger(module)
    if len(logger.handlers) == 0:
        logger.propagate = 0
        logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
                                      '%Y-%m-%d %H:%M:%S')
        logfile = fname
        rthandler = OSSRotatingFileHandler(logfile, maxBytes=maxfilesize * 1024 * 1024, backupCount=maxbackupcount)
        rthandler.setFormatter(formatter)
        logger.addHandler(rthandler)
    return logger


def checkAndCompressTrace(handler):
    traceFile = handler.filename
    if os.path.isfile(traceFile) and os.path.getsize(traceFile) >= handler.maxBytes:
        newFileName = '%s.%s' % (traceFile, str(int(time.time() * 1000000)))
        os.rename(traceFile, newFileName)
        handler.doRollover()


def getDummyLogger(module='default'):
    logger = logging.getLogger(module)
    if len(logger.handlers) == 0:
        logger.propagate = 0
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d(%(process)d|%(thread)d)[%(module)s:%(lineno)d]%(message)s', '%Y-%m-%d %H:%M:%S')
        rthandler = logging.StreamHandler(sys.stdout)
        rthandler.setFormatter(formatter)
        logger.addHandler(rthandler)
    return logger


def setLogger(moduleName, logger):
    global __defaultLoggers
    __defaultLoggers[moduleName] = logger


def setDefaultLogger(logger):
    setLogger('default', logger)


def getDefaultLogger():
    if not __defaultLoggers:
        try:
            _logger = getLogger()
        except Exception:
            _logger = getDummyLogger()
            _logger.exception('getDefaultLogger')

    else:
        fn, _lno, _func = findCaller()
        module = os.path.splitext(os.path.basename(fn))[0]
        if module not in __defaultLoggers:
            module = 'default'
        _logger = __defaultLoggers.get(module, getLogger())
    return _logger
