# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import functools
import inspect

from .common import *
from .datastructures import Context
from .exceptions import FieldError, DataError
from .transforms import import_loop, get_import_context
from .undefined import Undefined


__all__ = ['validate']


def validate(cls, instance_or_dict, trusted_data=None, partial=False, strict=False,
             convert=True, validate=True, oo=False, app_data=None, context=None):
    """
    Validate some untrusted data using a model. Trusted data can be passed in
    the `trusted_data` parameter.

    :param cls:
        The model class to use as source for validation. If given an instance,
        will also run instance-level validators on the data.
    :param instance_or_dict:
        A ``dict`` or ``dict``-like structure for incoming data.
    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :param strict:
        Complain about unrecognized keys. Default: False
    :param trusted_data:
        A ``dict``-like structure that may contain already validated data.
    :param convert:
        Controls whether to perform import conversion before validating.
        Can be turned off to skip an unnecessary conversion step if all values
        are known to have the right datatypes (e.g., when validating immediately
        after the initial import). Default: True

    :returns: data
        ``dict`` containing the valid raw_data plus ``trusted_data``.
        If errors are found, they are raised as a ValidationError with a list
        of errors attached.
    """
    context = context or get_validation_context(**locals())
    return import_loop(cls, instance_or_dict, context)


def validate_model(cls, data, context):
    """
    Validate data using model level methods.

    :param cls:
        The Model class to validate ``data`` against.

    :param data:
        A dict with data to validate. Invalid items are removed from it.

    :returns:
        Errors of the fields that did not pass validation.
    """
    errors = {}
    invalid_fields = []
    for field_name, field in iteritems(cls._fields):
        if field_name in cls._validators and field_name in data:
            value = data[field_name]
            try:
                cls._validators[field_name](cls, data, value, context)
            except FieldError as exc:
                field = cls._fields[field_name]
                serialized_field_name = field.serialized_name or field_name
                errors[serialized_field_name] = exc.messages
                invalid_fields.append(field_name)

    for field_name in invalid_fields:
        data.pop(field_name)

    return errors


def get_validation_context(**options):
    options['validate'] = True
    return get_import_context(**options)


def prepare_validator(func, argcount):
    if isinstance(func, classmethod):
        func = func.__get__(object).__func__
    if len(inspect.getargspec(func).args) < argcount:
        @functools.wraps(func)
        def newfunc(*args, **kwargs):
            if not kwargs or kwargs.pop('context', 0) is 0:
                args = args[:-1]
            return func(*args, **kwargs)
        return newfunc
    return func

