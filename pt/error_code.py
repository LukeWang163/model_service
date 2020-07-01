"""
modelarts service error code definition
"""
from collections import OrderedDict


class ModelArtsError(Exception):
    # Base class for AIS exceptions
    code_key = 'erno'
    msg_key = 'msg'
    code = NotImplemented
    msg = NotImplemented

    def to_dict(self):
        # convert to an OrderedDict that can be used to update json result
        return OrderedDict([[self.code_key, self.code], [self.msg_key, self.msg]])

    def __str__(self):
        return 'AISError: (%s, %s)' % (self.code, self.msg)


class MR0100(ModelArtsError):
    # Specific ModelArts error
    code = 'MR.0100'
    msg = 'Succeeded'


class MR0101(ModelArtsError):
    # Specific ModelArts error
    code = 'MR.0101'
    msg = 'The input parameter is invalid'


class MR0105(ModelArtsError):
    # Specific ModelArts error
    code = 'MR.0105'
    msg = 'Recognition failed'


__all__ = ['ModelArtsError', 'MR0100', 'MR0101', 'MR0105']
