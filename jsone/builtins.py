from __future__ import absolute_import, print_function, unicode_literals

import math
from .shared import string, to_str, fromNow, JSONTemplateError
import dateutil
from dateutil import parser
import dateutil.parser as dp

class BuiltinError(JSONTemplateError):
    pass

class RequiredValueError(Exception):
  """Required value is missing"""
  def __init__(self):
    Exception.__init__(self, "requied value is missing")


def build(context):
    builtins = {}

    def builtin(name, variadic=None, argument_tests=None, minArgs=None):
        def wrap(fn):
            def bad(reason=None):
                raise BuiltinError(
                    (reason or 'invalid arguments to builtin: {}').format(name))
            if variadic:
                def invoke(*args):
                    if minArgs:
                        if len(args) < minArgs:
                            bad("too few arguments to {}")
                    for arg in args:
                        if not variadic(arg):
                            bad()
                    return fn(*args)

            elif argument_tests:
                def invoke(*args):
                    if len(args) != len(argument_tests):
                        bad()
                    for t, arg in zip(argument_tests, args):
                        if not t(arg):
                            bad()
                    return fn(*args)

            else:
                def invoke(*args):
                    return fn(*args)

            builtins[name] = invoke
            return fn
        return wrap

    def is_number(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def is_string(v):
        return isinstance(v, string)

    def is_string_or_array(v):
        return isinstance(v, (string, list))

    def anything_except_array(v):
        return isinstance(v, (string, int, float, bool)) or v is None

    def anything(v):
        return isinstance(v, (string, int, float, list, dict)) or v is None or callable(v)

    # ---

    builtin('min', variadic=is_number, minArgs=1)(min)
    builtin('max', variadic=is_number, minArgs=1)(max)
    builtin('sqrt', argument_tests=[is_number])(math.sqrt)
    builtin('abs', argument_tests=[is_number])(abs)
    builtin('int', minArgs=1)(int)

    @builtin('ceil', argument_tests=[is_number])
    def ceil(v):
        return int(math.ceil(v))

    @builtin('floor', argument_tests=[is_number])
    def floor(v):
        return int(math.floor(v))

    @builtin('lowercase', argument_tests=[is_string])
    def lowercase(v):
        return v.lower()

    @builtin('uppercase', argument_tests=[is_string])
    def lowercase(v):
        return v.upper()

    builtin('len', argument_tests=[is_string_or_array])(len)
    builtin('str', argument_tests=[anything_except_array])(to_str)

    @builtin('strip', argument_tests=[is_string])
    def strip(s):
        return s.strip()

    @builtin('rstrip', argument_tests=[is_string])
    def rstrip(s):
        return s.rstrip()

    @builtin('lstrip', argument_tests=[is_string])
    def lstrip(s):
        return s.lstrip()

    @builtin('custom_fields', argument_tests=[is_string_or_array])
    def add_custom_fields(custom_fields_array):
        formated_custom_fields = {}
        if len(custom_fields_array) > 0:
            for custom_field in custom_fields_array:
                if custom_field['ff_coltype'] == 'date':
                    custom_field_value = iso_to_utc(custom_field['field_value'])
                else:
                    custom_field_value = custom_field['field_value']
                formated_custom_fields[custom_field['ff_name']] = custom_field_value
        return formated_custom_fields

    @builtin('custom_fields_generic', argument_tests=[is_string_or_array])
    def add_custom_fields_generic(custom_fields_array):
        formated_custom_fields = {}
        if len(custom_fields_array) > 0:
            for custom_field in custom_fields_array:
                if custom_field['type'] == 'date':
                    custom_field_value = iso_to_utc(custom_field['value'])
                else:
                    custom_field_value = custom_field['value']
                formated_custom_fields[custom_field['column']] = custom_field_value
        return formated_custom_fields

    @builtin('calculate_chrs')
    def calculate_chrs(start_time, end_time):
        if start_time is None or end_time is None:
            return None
        start_time_converted = dateutil.parser.parse(start_time)
        end_time_converted = dateutil.parser.parse(end_time)
        difference_time = end_time_converted - start_time_converted
        return int(difference_time.total_seconds() * 1000)

    @builtin('iso_to_utc')
    def iso_to_utc(iso_time, format='%Y-%m-%d %H:%M:%S %Z'):
        if iso_time is None:
            return iso_time
        datetime_object = dateutil.parser.parse(iso_time)
        return datetime_object.strftime(format)

    @builtin('iso_to_epoch')
    def iso_to_epoch(iso_timestamp):
        if iso_timestamp is None:
            return iso_timestamp
        time = dp.parse(iso_timestamp).strftime('%s.%f')
        return int(float(time) * 1000)

    @builtin('get')
    def get(args, key):
        try:
            if key in args:
                return args[key]
            else:
                return None
        except:
            return None

    
    @builtin('required_value')
    def required_value(key_value):
        if key_value is None:
            raise RequiredValueError
        elif isinstance(key_value, string) and len(key_value) == 0:
            raise RequiredValueError
        else:
            return key_value

    @builtin('multiply_number')
    def multiply_number(number, factor):
        return int(number * factor)

    @builtin('divide_number')
    def divide_number(number, factor):
        if (factor == 0 or factor == None):
            raise ZeroDivisionError
        else:
            if number == None:
                return None
            else:
                return int(number / factor)

    @builtin('only_one_key_present')
    def only_one_key_present(dictionary, key):
        if len(dictionary) == 1 and key in dictionary:
            return True
        else:
            return False

    @builtin('fromNow', variadic=is_string, minArgs=1)
    def fromNow_builtin(offset, reference=None):
        return fromNow(offset, reference or context.get('now'))

    @builtin('typeof', argument_tests=[anything])
    def typeof(v):
        if isinstance(v, bool):
            return 'boolean'
        elif isinstance(v, string):
            return 'string'
        elif isinstance(v, (int, float)):
            return 'number'
        elif isinstance(v, list):
            return 'array'
        elif isinstance(v, dict):
            return 'object'
        elif v is None:
            return None
        elif callable(v):
            return 'function'

    return builtins
