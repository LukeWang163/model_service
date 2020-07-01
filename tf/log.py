import logging
# logging to both file and stdout
import sys
level = logging.INFO
logFormatter = logging.Formatter(
    fmt="%(asctime)s [%(threadName)-12.12s] - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z")
fileHandler = logging.FileHandler("../.tf.log")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(level)

consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(level)

root = logging.getLogger()
root.addHandler(fileHandler)
root.addHandler(consoleHandler)


def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
