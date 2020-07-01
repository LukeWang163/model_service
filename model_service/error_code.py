"""
modelarts service error code definition
"""
from collections import OrderedDict

import log

logger = log.getLogger(__name__)


class ModelArtsError(Exception):
    """Base class for AIS exceptions"""
    code_key = 'erno'
    msg_key = 'msg'
    code = NotImplemented
    msg = NotImplemented

    def to_dict(self):
        """convert to an OrderedDict that can be used to update json result"""
        return OrderedDict([[self.code_key, self.code],
                            [self.msg_key, self.msg]])

    def __str__(self):
        return 'ModelArtsError: (%s, %s)' % (self.code, self.msg)


class PY0100(ModelArtsError):
    """Specific ModelArts error"""
    code = 'PY.0100'
    msg = 'Succeeded'


class PY0101(ModelArtsError):
    """Specific ModelArts error"""
    code = 'PY.0101'
    msg = 'Input data is invalid'


class PY0105(ModelArtsError):
    """Specific ModelArts error"""
    code = 'PY.0105'
    msg = 'Inference failed'


__all__ = ['ModelArtsError', 'PY0100', 'PY0101', 'PY0105']
