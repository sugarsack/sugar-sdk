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


    def get_module_toc(self) -> str:
        """
        Get module TOC.

        :return: rendered TOC
        """

        doc_header = self._docmap.get("doc", {}).get("module", {})
        template = sugarsdk.utils.get_template("doc_m_idx_{}".format(self._mod_type))
        func_list = self._docmap.get("doc", {}).get("tasks")

        if func_list:
            m_doc = type("mdoc", (), {
                "uri": self._mod_uri, "author": doc_header.get("author", "N/A"),
                "description": doc_header.get("synopsis", "N/A"), "summary": doc_header.get("summary"),
                "version_added": doc_header.get("since_version", "N/A"),
                "f_docs": ["doc_f_{}".format(_uri.replace(".", "_")) for _uri in func_list],
            })
            out = jinja2.Template(template).render(m_doc=m_doc, filters=self.filters, len=len)
        else:
            out = None

        return out


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
