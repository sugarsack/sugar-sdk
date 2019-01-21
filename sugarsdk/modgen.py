#!/usr/bin/env python3

import os
import sys
import platform
import argparse
import sugar.modules.states
import sugar.modules.runners
import sugar.lib.exceptions
import jinja2


class BaseModuleResource:
    """
    """
    def __init__(self, sdk_root):
        self._sdk_root = sdk_root

    def _get_template(self, name):
        with open(os.path.join(self._sdk_root, "stubs/{}.jinja2".format(name))) as thl:
            return thl.read()

    def _get_common_resource(self, prefix, resource, namespace):
        """
        Get corresponding resource and apply the namespace.
        """
        return jinja2.Template(self._get_template("{}_{}".format(prefix, resource))).render(**namespace)

class StateModuleResources(BaseModuleResource):
    """
    """
    def get_resource(self, resource):
        """
        Get corresponding resource and apply the namespace.
        """
        return self._get_common_resource("state", resource, namespace)

class RunnerModuleResources(BaseModuleResource):
    """
    Resources of the runner module.
    """
    def get_resource(self, resource, namespace):
        """
        Get corresponding resource and apply the namespace.
        """
        return self._get_common_resource("runner", resource, namespace)


class ModuleGenerator:
    RS_DOCUMENTATION = "doc"
    RS_EXAMPLES = "examples"
    RS_INIT = "init"
    RS_INTERFACE = "interface"
    RS_IMPLEMENTATION = "impl"

    def __init__(self, args):
        self._cli_args = args
        self.rs_runner = RunnerModuleResources(sdk_root="./sugar-sdk")
        self.rs_state = StateModuleResources(sdk_root="./sugar-sdk")

    def _get_module_path(self):
        """
        Get module path.
        
        :raises SugarException: if unable to find the path.
        :returns: path to the module without the module name
        """
        if self._cli_args.type == "runner":
            path = sugar.modules.runners.__file__
        elif self._cli_args.type == "state":
            path = sugar.modules.runners.__file__
        else:
            raise sugar.lib.exceptions.SugarException("Type expected either to be 'runner' or 'state'.")
        if not self._cli_args.name:
            raise sugar.lib.exceptions.SugarException("Name of the module was not specified.")

        return os.path.join(os.path.dirname(path), *self._cli_args.name.split("."))

    def _add_resource(self, root, rs_name):
        """
        Add a resource stub.
        """
        mod_name = self._cli_args.name.rsplit(".", 1)[-1]
        mod_namespace = self._cli_args.name.rsplit(".", 1)[0]
        namespace = {
            "mod_name": mod_name,
            "mod_author": "You Great <you@great.org>",
            "mod_summary": "One-liner about what your module is about",
            "mod_synopsis": "Some more lines about this module.",
            "mod_type": "{}s".format(self._cli_args.type),
            "sugar_version": "0.0.0",
            "mod_namespace": mod_namespace,
        }

        name_map = {
            "init": "__init__.py",
            "examples": "examples.yaml",
            "doc": "doc.yaml",
            "impl": "{}.py".format(self._cli_args.impl),
            "interface": "interface.py"
        }

        try:
            resource = getattr(self, "rs_{}".format(self._cli_args.type)).get_resource(rs_name, namespace)
            with open(os.path.join(root, name_map[rs_name]), "w") as h_res:
                h_res.write(resource)
            #print(root, name_map[rs_name])
        except Exception as exc:
            print("Failed to process '{}': {}".format(rs_name, exc))
            sys.exit(1)

    def _add_inits_over(self, root):
        """
        Add __init__.py files all across the root from "sugar/modules/<type/..." onwards.
        """
              
        mod_type = "{}s".format(self._cli_args.type)
        while True:
            if not os.path.exists(os.path.join(root, "__init__.py")):
                self._add_resource(root, "init")
            root = os.path.abspath(os.path.join(root, os.pardir))
            if root.endswith(mod_type):
                break

    def _create_tree(self, root):
        """
        Create a tree of the module, if it does not exists yet.
        """

        if not os.path.exists(root):
            os.makedirs(root)
            for rs_name in [self.RS_INIT, self.RS_EXAMPLES, self.RS_DOCUMENTATION, self.RS_INTERFACE]:
                self._add_resource(root, rs_name)
            root = os.path.join(root, "_impl")
            os.mkdir(root)
            self._add_resource(root, self.RS_INIT)
            self._add_resource(root, self.RS_IMPLEMENTATION)

    def generate(self):
        """
        Generate a module (runner or state).
        """
        mod_path = self._get_module_path()
        self._create_tree(mod_path)
        self._add_inits_over(mod_path)
        print("generated to", mod_path)
