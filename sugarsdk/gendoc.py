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
        self.loader = SugarModuleLoader()  # We're not generating anything for the custom modules.
        self.out = ConsoleMessages()

    def generate(self) -> None:
        """
        Generate a documentation.

        :returns: None
        """
        self.out.info("Generating documentation for {} modules", "runner")
        self.out.info("  - collecting TOC")
        mod_toc = type("mod_toc", (), {"mod_runner": [], "mod_state": []})
        for uri in sorted(self.loader.runners.map().keys()):
            self.out.info("  - create module TOC for {}", uri)

            toc_name = "doc_m_toc_{}".format(uri.replace(".", "_"))
            mod_toc.mod_runner.append(toc_name)
            mod_rst_doc = ModRSTDoc(uri, mod_type="runner")

            self.out.info("  - write module TOC ({})", toc_name)
            with sugar.utils.files.fopen("{}.rst".format(toc_name), "w") as toc_h:
                toc_h.write(mod_rst_doc.get_module_toc())

        self.out.info("  - write reference TOC ({})", toc_name)
        with sugar.utils.files.fopen("modbook.rst", "w") as mbh:
            mbh.write(jinja2.Template(sugarsdk.utils.get_template("doc_modbook")).render(mod_toc=mod_toc, len=len))
