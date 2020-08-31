"""
modelarts service error code definition
"""
from collections import OrderedDict

import log

logger = log.getLogger(__name__)


class IMLPError(Exception):
    """Base class for IMLP exceptions"""
    code_key = 'errorCode'
    msg_key = 'errorMsg'
    code = NotImplemented
    msg = NotImplemented

    def to_dict(self):
        """convert to an OrderedDict that can be used to update json result"""
        return OrderedDict([[self.code_key, self.code],
                            [self.msg_key, self.msg]])

    def __str__(self):
        return 'ModelArtsError: (%s, %s)' % (self.code, self.msg)


class PY0200(IMLPError):
    code = 'PY.0200'
    msg = 'Succeeded'


class PY0101(IMLPError):
    code = 'PY.0101'
    msg = 'Input data is invalid'


class PY0105(IMLPError):
    code = 'PY.0105'
    msg = 'Inference failed'


__all__ = ['IMLPError', 'PY0200', 'PY0101', 'PY0105']
