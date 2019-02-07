# coding: utf-8
"""
Module documentation generator.

Generates sort of online book out of the validated modules
and their documentaiton.
"""
import os
import jinja2
import textwrap

import terminaltables
import sugarsdk.utils
import sugar.utils.files

from sugar.components.docman.docrnd import ModDocBase
from sugar.components.docman.jinfilters import JinjaRstFilters
from sugar.lib.loader import SugarModuleLoader
from sugar.lib.outputters.console import ConsoleMessages


class ModRSTDoc(ModDocBase):
    """
    Generate RST documentation.
    """
    filters = JinjaRstFilters()

    def _to_rst_header_table(self, table:str) -> str:
        """
        Hack to quickly add header on Ascii table for rst.

        :param table: table header
        :return: table data with the header
        """
        data = table.split(os.linesep)
        data[2] = data[2].replace("-", "=")

        return os.linesep.join(data)

    def _wrap_description(self, descr: list) -> str:
        """
        Wrap description.

        :param descr: description
        :return: wrapped description
        """
        return " ".join(textwrap.wrap(" ".join(descr), 40))

    def _get_params_table(self, f_name: str) -> str:
        """
        Make parameters table.

        :param f_name: function name.
        :return: rendered parameters table (RST version)
        """
        table_data = [
            ["Parameter", "Purpose"],
        ]
        tbl = terminaltables.AsciiTable(table_data=table_data)
        tbl.inner_row_border = True
        f_docmap = self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {})
        for param in f_docmap.get("parameters", {}):
            param_data = f_docmap["parameters"][param]
            _req = "**required**" if param_data.get("required") else "*optional*"
            _type = "type: ```{}```".format(param_data.get("type", "*object*"))
            _opt = "" if "default" not in param_data else "\n\ndefault: ```{}```".format(param_data["default"])
            table_data.append(
                [
                    "```{p}```\n\n{r}\n\n{t}{o}".format(p=param, r=_req, t=_type, o=_opt),
                    self._wrap_description(param_data.get("description", "N/A"))
                ]
            )

        return self._to_rst_header_table(tbl.table)

    def _get_cli_example_usage(self, f_name: str) -> tuple:
        """
        Get CLI example usage.

        :param f_name: function name.
        :return: CLI example usage string
        """
        examples = self._docmap.get("examples", {}).get(f_name, {})
        return (self._wrap_description(examples.get("description", "")),
                textwrap.indent(examples.get("commandline"), "   "))

    def _get_state_example_usage(self, f_name: str) -> str:
        """
        Get state example usage.

        :param f_name: function name.
        :return: state example usage string
        """
        examples = self._docmap.get("examples", {}).get(f_name, {})
        return textwrap.indent(examples.get("states"), "   ")

    def _get_return_data_table(self, f_name: str) -> str:
        """
        Get return data table.

        :param f_name: function name
        :return: rendered table of the returning data
        """

    def get_function_manual(self, f_name: str) -> str:
        """
        Get function manual.

        :param f_name: function name.
        :return: rendered manual data
        """
        template = sugarsdk.utils.get_template("doc_m_func_{}".format(self._mod_type))
        f_docmap = self._docmap.get("doc", {}).get("tasks", {}).get(f_name, {})

        example_descr, cli_example = self._get_cli_example_usage(f_name=f_name)
        f_doc = type("fdoc", (), {
            "uri": "{}.{}".format(self._mod_uri, f_name),
            "description": f_docmap.get("description", "N/A"),
            "example_description": example_descr,
            "cli_caption": "Command line",
            "cli_caption_anchor": "{}_{}_cli_example".format(self._mod_uri.replace(".", "_"), f_name),
            "cli_example": cli_example,
            "state_caption": "Example state",
            "state_caption_anchor": "{}_{}_state_example".format(self._mod_uri.replace(".", "_"), f_name),
            "state_example": self._get_state_example_usage(f_name=f_name),
            "t_params": self._get_params_table(f_name=f_name),
            "t_return_data": self._get_return_data_table(f_name=f_name),
        })

        return jinja2.Template(template).render(f_doc=f_doc, len=len)

    def next_func(self):
        """
        Iterate over function manual

        :return: iterator
        """
        for f_name in self._docmap.get("doc", {}).get("tasks", {}):
            yield f_name, self.get_function_manual(f_name=f_name)

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

            self.out.info("  - generating module function manuals")
            for doc_func_fname, doc_func_man in mod_rst_doc.next_func():
                self.out.info("  - writing function manual for {}".format(doc_func_fname))
                with sugar.utils.files.fopen("doc_f_{}.rst".format(doc_func_fname), "w") as fh_h:
                    fh_h.write(doc_func_man)
                    #print(">>>", doc_func_fname)
                    #print(doc_func_man)

        self.out.info("  - write reference TOC ({})", toc_name)
        with sugar.utils.files.fopen("doc_idx_modbook.rst", "w") as mbh:
            mbh.write(jinja2.Template(sugarsdk.utils.get_template("doc_modbook")).render(mod_toc=mod_toc, len=len))
