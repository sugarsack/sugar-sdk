# coding: utf-8
"""
Module documentation generator.

Generates sort of online book out of the validated modules
and their documentaiton.
"""
from sugar.components.docman.docrnd import ModDocBase
from sugar.components.docman.jinfilters import JinjaRstFilters


class ModRSTDoc(ModDocBase):
    """
    Generate RST documentation.
    """
    filters = JinjaRstFilters()


class ModuleDocumentationGenerator:
    """
    Module documentaiton generator class.
    """

    def __init__(self, args):
        self._args = args

    def generate(self) -> None:
        """
        Generate a documentation.

        :returns: None
        """
