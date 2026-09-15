"""A clean sample: short functions, shallow nesting, stdlib-only imports."""
import json
import os


def read_config(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def merged(base, override):
    result = dict(base)
    result.update(override)
    return result
