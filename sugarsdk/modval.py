# coding: utf-8
"""
Sugar Module validator.

Author: Bo Maryniuk <bo@maryniuk.net>

Validates all the modules for their consistency
and checks if the external documentation, schemas etc
looks legit.
"""
import os
import astroid

import sugar.modules.runners
import sugar.modules.states
import sugar.utils.files

from sugar.lib.compat import yaml
from sugar.lib.loader.virtual import VirtualModuleLoader
from sugar.lib.loader.simple import SimpleModuleLoader
from sugar.lib.outputters.console import ConsoleMessages


class ModuleValidator:
    """
    Module validator.
    """
    def __init__(self, args):
        self._cli_args = args
        self._runner_module_loader = VirtualModuleLoader(sugar.modules.runners)
        self._state_module_loader = SimpleModuleLoader(sugar.modules.states)
        self._console = ConsoleMessages()

        self.infos = []
        self.warnings = []
        self.errors = []

    def _get_runner_meta(self, uri):
        """
        Get doc, schema and examples of a runner.

        :param uri:
        :return:
        """
        mod_type = self._cli_args.type
        mod_path = os.path.join(self._runner_module_loader.root_path, os.path.sep.join(uri.split(".")))

        doc_path = os.path.join(mod_path, "doc.yaml")
        xpl_path = os.path.join(mod_path, "examples.yaml")
        scm_path = os.path.join(mod_path, "scheme.yaml")

        for metafile in [doc_path, xpl_path, scm_path]:
            if not os.path.exists(metafile):
                self.errors.append("{} module at '{}' is missing '{}' file!".format(
                    mod_type.title(), uri, metafile))

        meta = {}
        for metakey, metafile in [("doc", doc_path), ("example", xpl_path), ("scheme", scm_path)]:
            with sugar.utils.files.fopen(metafile) as mth:
                try:
                    meta[metakey] = yaml.load(mth.read())
                except Exception as exc:
                    meta[metakey] = None
                    self.warnings.append("'{}' in {} module seems broken ({})".format(
                        os.path.basename(metafile), mod_type, exc))
        return meta

    def _get_runner_interface(self, uri):
        """
        Get parsed runner interface source.

        :param uri:
        :return:
        """
        ifc = {}
        ifc_path = os.path.join(self._runner_module_loader.root_path, os.path.sep.join(uri.split(".")), "interface.py")
        with sugar.utils.files.fopen(ifc_path) as src_h:
            ifc["interface"] = astroid.parse(src_h.read())
        return ifc

    def _get_runner_implementations(self, uri):
        """
        Get parsed runner implementations source.

        :param uri:
        :return:
        """
        imps = {}
        imp_path = os.path.join(self._runner_module_loader.root_path, os.path.sep.join(uri.split(".")), "_impl")
        for fname in os.listdir(imp_path):
            if fname.startswith("_"):
                continue
            with sugar.utils.files.fopen(os.path.join(imp_path, fname)) as src_h:
                imps[fname] = astroid.parse(src_h.read())
        return imps

    def _runner_cmp_meta(self, ifc, meta, uri):
        """
        Compare meta to the interface.

        :param ifc: interface
        :param meta: meta (doc/examples/scheme)
        :param uri: URI of the module.
        :return:
        """
        mod_type = self._cli_args.type
        methods = []
        for node in ifc["interface"].body:
            if isinstance(node, astroid.ClassDef):
                for func_node in node.body:
                    methods.append(func_node)

        self._console.info("Verifying scheme")
        scheme = meta.get("scheme")
        self._console.warning("  (unsupported yet)")

        self._console.info("Verifying documentation")
        doc = meta.get("doc")

        tasks = doc.get("tasks")
        if tasks is None:
            self.errors.append("Documentation in '{}' {} module has no 'tasks' section".format(uri, mod_type))

        ifc_method_names = set()
        for mtd in methods:
            ifc_method_names.add(mtd.name)
            if mtd.name not in tasks:
                self.errors.append("Function '{}' is not documented in {} module".format(mtd.name, mod_type))
            is_abstract = False
            if mtd.decorators is not None:
                for decorator in mtd.decorators.nodes:
                    if decorator.attrname == "abstractmethod":
                        is_abstract = True
                        break
            if not is_abstract:
                self.errors.append("Function '{}' is not abstract in the {} module interface".format(mtd.name, mod_type))

            self._common_cmp_signature(uri, mtd, tasks.get(mtd.name, {}))

        for task in tasks:
            if task not in ifc_method_names:
                self.errors.append("Documentation in '{}' {} module contains superfluous data. "
                                   "The interface has less methods than "
                                   "the documentation describes".format(uri, mod_type))
                break

        self._console.info("Verifying examples")
        examples = meta.get("examples")

    def _common_cmp_signature(self, uri, node, doc):
        """
        Compare if the function is the same as the documentation.

        :param node: astroid function node object
        :param doc: documentation for that node
        :return: None
        """
        mod_type = self._cli_args.type
        if "parameters" not in doc:
            self.errors.append("Documentation of the {} module '{}' has no parameters section".format(mod_type, uri))

        if node.args.vararg:
            self.infos.append("Not so good: implicit arguments (varargs) are discouraged. "
                              "Consider explicitly defining your parameters instead, or make few more methods.")
        if node.args.kwarg:
            self.infos.append("Not so good: implicit keyword arguments are discouraged. "
                              "Consider explicitly defining your keyword parameters or split to more methods.")
        node_args = []
        for arg in node.args.args:
            if arg.name in ["self", "cls"]:
                continue
            elif arg.name not in doc.get("parameters", {}):
                self.errors.append("Documentation of the {} module '{}' "
                                   "should explain what parameter '{}' in function '{}' is for.".format(
                                       mod_type, uri, arg.name, node.name))
            elif "description" not in doc.get("parameters", {}).get(arg.name, {}):
                self.errors.append("Documentation of the {} module '{}' "
                                   "is missing description of the parameter '{}' in function '{}'.".format(
                                       mod_type, uri, arg.name, node.name))
            node_args.append(arg)
        # Get a map of non-required attrs in signature
        sig_defaults = list(dict(zip([arg.name for arg in node_args][::-1],
                                     [False for item in node.args.defaults])).keys())
        sig_default_values = dict(zip([arg.name for arg in node_args][::-1],
                                      [item.value for item in node.args.defaults]))
        # Get a map of required attrs in doc
        doc_req = {}
        for p_name, p_doc in doc.get("parameters", {}).items():
            if p_name in sig_default_values:
                if p_doc.get("default") != sig_default_values.get(p_name):
                    self.warnings.append("Parameter '{}' in task '{}' of the {} module '{}' "
                                         "should be documented as default to '{}'.".format(
                        p_name, node.name, mod_type, uri, sig_default_values.get(p_name)))
            doc_req[p_name] = p_doc.get("required", False)

        for arg in node_args:
            if arg.name not in sig_defaults and not doc_req.get(arg.name, False):
                self.errors.append("Argument '{}' of the function '{}' in the {} module "
                                   "'{}' should be documented as required.".format(arg.name, node.name, mod_type, uri))
            elif arg.name in sig_defaults and doc_req.get(arg.name, True):
                self.errors.append("Argument '{}' of the function '{}' in the {} module "
                                   "'{}' should be documented as optional.".format(arg.name, node.name, mod_type, uri))

    def _runner_cmp_impl(self, ifc, impl, uri):
        """
        Compare implementations to the interface.

        :param ifc: interface
        :param impl: implementations
        :param uri: URI of the module
        :return:
        """

    def _validate_runner_by_uri(self, uri):
        """
        Validate a runner module by uri.

        :param uri:
        :return: tuple of infos warnings and errors
        """
        meta = self._get_runner_meta(uri)
        self._console.info("  ...get meta ({})", ', '.join(list(meta.keys())))
        interface = self._get_runner_interface(uri)
        self._console.info("  ...get interface")
        implementations = self._get_runner_implementations(uri)
        self._console.info("  ...get implementations ({})", len(implementations))

        self._runner_cmp_meta(interface, meta, uri)
        self._runner_cmp_impl(interface, implementations, uri)

        self._console.info("Done verification.")

    def _validate_state_by_uri(self, uri):
        """
        Validate a state module by uri.

        :param uri:
        :return: tuple of infos warnings and errors
        """

    def validate(self):
        """
        Validate modules.

        :return: None
        """
        ret = False
        if self._cli_args.all:
            self._console.warning("Validation of {} is not yet implemented", "all modules")
            ret = True
        elif self._cli_args.name is not None:
            self._console.info("Validating '{}' module", self._cli_args.name)
            if self._cli_args.type == "runner":
                self._validate_runner_by_uri(self._cli_args.name)
                ret = True
            elif self._cli_args.type == "state":
                self._validate_state_by_uri(self._cli_args.name)
                ret = True

        if not ret:
            self._console.error("Don't know what/how to validate for you...")

        return ret

    def report(self):
        """
        Print report and return an exit code.

        :return:
        """
        self._console.info("\nReport:\n")
        for idx, msg in enumerate(self.infos):
            self._console.info("  {}. {}".format(idx + 1, msg))
        for idx, msg in enumerate(self.warnings):
            self._console.warning("  {}. {}".format(idx + 1, msg))
        for idx, msg in enumerate(self.errors):
            self._console.error("  {}. {}".format(idx + 1, msg))

        failed = int(bool(self.errors + self.warnings))
        if not failed:
            self._console.warning("  All seems to be OK!\n")
        else:
            self._console.warning("\nPlease fix these issues.")

        return failed
