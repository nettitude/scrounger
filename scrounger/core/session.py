"""
Module that holds all information of a session of scrounger
"""

# custom module imports
from sys import path as _path

# config imports
from scrounger.utils.config import _SCROUNGER_HOME

class Session(object):

    _name           = ""
    _rows, _columns = 128, 80

    options         = {}
    global_options  = {}
    devices         = {}
    results         = {}
    exceptions      = [] # unused

    _available_modules = None
    _module_instance   = None
    _current_module    = None
    _module_class      = None

    prompt             = None

    def __init__(self, name):
        from os import popen, path

        # helper functions
        from scrounger.utils.general import execute

        # used to find the available modules
        import scrounger.modules

        self._name = name

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

        # public vars to be used by calling modules
        self.options = {}
        self.global_options  = {
            "debug":   "False",
            "device":  "",
            "output":  "",
            "verbose": "False"
        }

        self.devices = {}
        self.results = {}
        self.exceptions = [] # unused
        self.prompt = None

        # initialize private vars
        self._module_instance = None
        self._current_module = None
        self._module_class = None

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

    def name(self):
        """
        Returns the name of a session

        :return: a str with the session name
        """
        return self._name

    def to_dict(self):
        """
        Returns a dict representing the current sesssion

        :return:  a dict representing the session
        """
        return {
            "name": self._name,
            "devices": [
                {
                    "id": self.devices[device]["device"].device_id(),
                    "type": self.devices[device]["type"],
                    "no": device
                } for device in self.devices
            ],
            "results": self.results, # TODO: if object, need to reproduce it
            "global": self.global_options,
            "options": self.options,
            "current": self._current_module,
            "prompt": self.prompt
        }

    def __str__(self):
        return "Session {}".format(self.name())


def load_sessions(filename):
    """
    Loads a list of sessions from a file

    :param str filename: the file path to load the sessions from
    :return: a list of Session objects
    """
    from scrounger.core.device import IOSDevice, AndroidDevice
    from scrounger.utils.general import file_exists
    from json import loads

    if not file_exists(filename):
        return []

    with open(filename, "r") as fp:
        content = fp.read()

    sessions = []

    try:
        json_sessions = loads(content)
    except Exception as e:
        # error loading sessions files
        return []

    for json_session in json_sessions["sessions"]:
        session = Session(json_session["name"])
        for json_device in json_session["devices"]:
            if json_device["type"] == "ios":
                device = IOSDevice(json_device["id"])
            else:
                device = AndroidDevice(json_device["id"])
            session.devices[json_device["no"]] = {
                "device": device,
                "type": json_device["type"]
            }
        session.results = json_session["results"]
        session.global_options = json_session["global"]
        session.options = json_session["options"]
        if json_session["current"]:
            session.use(json_session["current"])

        session.prompt = json_session["prompt"]

        sessions += [session]

    return sessions

def save_sessions(sessions, filename):
    """
    Saves a list of session into a file

    :param list sessions: a list of Session objects
    :param str filename: the filepath to save the sessions to
    :return: nothing
    """
    from json import dumps

    with open(filename, "w") as fp:
        fp.write(dumps(
            {"sessions": [session.to_dict() for session in sessions]}
        ))

