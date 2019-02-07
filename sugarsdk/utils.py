# coding: utf-8
"""
General utilities for the performing generic tasks.
"""
import os


def get_template(name):
    """
    Get a jinja template.

    :param name:
    :return:
    """
    with open(os.path.join(os.path.dirname(__file__), "stubs/{}.jinja2".format(name))) as thl:
        return thl.read()
