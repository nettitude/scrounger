"""
Module that holds all information of a session of scrounger

TODO: Make it be used by console modules
"""

# custom module imports
from sys import path as _path

# config imports
from scrounger.utils.config import _SCROUNGER_HOME


class Session(object):

    _name           = ""
    _rows, _columns = 128, 80

    options         = {}
    global_options  = {
        "debug":   "False",
        "device":  "",
        "output":  "",
        "verbose": "False"
    }
    devices         = {}
    results         = {}
    exceptions      = [] # unused

    _available_modules = None
    _module_instance   = None
    _current_module    = None
    _module_class      = None

    def __init__(self, name):
        from os import popen, path

        # helper functions
        from scrounger.utils.general import execute

        # used to find the available modules
        import scrounger.modules

        self._rows, self._columns  = popen('stty size', 'r').read().split()
        self._rows, self._columns  = int(self._rows), int(self._columns)
        if self._columns < 128: self._columns = 128

        # need to add / to then replace it
        modules_path = "{}/".format(scrounger.modules.__path__[0])
        modules = execute("find {} -name '*.py'".format(modules_path))

        self._available_modules = [
            module.replace(modules_path, "").replace(".py", "")
            for module in modules.split("\n")
            if module and "__" not in module
        ]

        # add custom modules
        modules_path = "{}/modules/".format(_SCROUNGER_HOME)
        modules = execute("find {} -name \"*.py\"".format(modules_path))

        # add path to sys.path
        _path.append(modules_path)

        self._available_modules += [
            module.replace(modules_path, "").replace(".py", "")
            for module in modules.split("\n")
            if module and "__" not in module
        ]

        # fix for macos
        self._available_modules = [
            module[1:] if module.startswith("/") else module
            for module in sorted(self._available_modules)
        ]

    def modules(self):
        """
        Returns the available modules

        :return: returns a list with the available modules
        """
        return self._available_modules

    def back(self):
        """Returns to the main state"""
        self._module_instance = None
        self._current_module = None
        self._module_class = None

    def use(self, module):
        self._current_module = module

        if module.startswith("custom/"):
            self._module_class = __import__("{}".format(
                module.replace("/", ".")), fromlist=["Module"])
        else:
            self._module_class = __import__("scrounger.modules.{}".format(
                module.replace("/", ".")), fromlist=["Module"])

        if not hasattr(self._module_class, "Module"):
            self._current_module = None
            self._module_class = None
            raise Exception("Missing `Module` class")

        self._module_instance = self._module_class.Module()

        if not hasattr(self._module_class.Module, "meta") or not hasattr(
            self._module_instance, "options"):
            self._module_instance = None
            self._current_module = None
            self._module_class = None
            raise Exception("Missing required variables")


    def module_options(self):
        """
        Returns the options dict for the current module or None if no module
        is active

        :return: a dict with the required options
        """
        if self._module_instance:
            return self._module_instance.options

        return None

    def module(self):
        """
        Returns the current active module or None if no module is active

        :return: a str with the current module
        """
        return self._current_module

    def instance(self):
        """
        Returns an instance with the current active module or None if no module
        is active

        :return: an object representing an inatance of the current active module
        """
        return self._module_instance
