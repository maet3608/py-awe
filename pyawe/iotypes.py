"""
Data types and their validation functions.
"""
from __future__ import absolute_import, print_function


def is_any(data):
    return True


def is_boolean(data):
    return isinstance(data, bool)


def is_number(data):
    return isinstance(data, int) or isinstance(data, float)


def IMPLEMENT_THIS(data):
    return False


IOTYPES = {
    'boolean': is_boolean,
    'number': is_number,
    'image_dataurl': IMPLEMENT_THIS,
    'any': is_any
}


def verify(iotype, data):
    if iotype not in IOTYPES:
        raise ValueError('Unknown data type')
    if not IOTYPES[iotype](data):
        raise ValueError('Data is of wrong type')
    return True
