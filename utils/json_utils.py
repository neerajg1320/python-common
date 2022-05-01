import json


def object_to_json_str(object, pretty=False):
    indent = 4 if pretty else None
    return json.dumps(object, indent=indent, default=str)


def json_str_to_object(json_str):
    return json.loads(json_str)