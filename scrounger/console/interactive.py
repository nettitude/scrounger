#! /usr/bin/env python
from __future__ import print_function
from cmd import Cmd as _Cmd
import signal as _signal

# custom module imports
from sys import path as _path

# scrounger imports
from scrounger.utils.config import Log, _HOME
from scrounger.utils.config import _SESSION_FILE, _HISTORY_FILE, _MAX_HISTORY

# session imports
from scrounger.core.session import Session as _Session
from scrounger.core.session import save_sessions as _save_sessions
from scrounger.core.session import load_sessions as _load_sessions

# change delimters for CMD
import readline

class Color():
    RED = "\033[31m"
    GREEN = "\033[32m"
    NORMAL = "\033[0m"
    UNDERLINE = "\033[4m"

class _ScroungerPrompt(_Cmd, object):
    _session = None
    _sessions = []

    def _print_error(self, msg):
        print("[-] {}".format(msg))

    def _print_status(self, msg):
        print("[+] {}".format(msg))

    def default(self, line):
        print("{}: command not found".format(line))

    def preloop(self):
        from os import popen, path
        from scrounger.utils.general import execute
        import scrounger.modules

        _Cmd.preloop(self) # sets up command completion

        self._session = _Session("default")
        self._session.prompt = self.prompt

        self._sessions = _load_sessions(_SESSION_FILE)

        readline.set_completer_delims(' \t\n')
        if path.exists(_HISTORY_FILE):
            readline.read_history_file(_HISTORY_FILE)

    def postloop(self):
        _Cmd.postloop(self)   ## Clean up command completion

        try:
            readline.set_history_length(_MAX_HISTORY)
            readline.write_history_file(_HISTORY_FILE)
        except:
            # readline is returning Exception for some reason
            pass

    def _print_list(self, header, list_items, description=None):
        """ Prints a list according to the screen size """

        if description:
            print("\n{}:".format(description))

        # calculate max lens
        lens = {}
        for key in header:
            max_len = len(str(header[key])) + 2
            for item in list_items:
                max_len = max(max_len, len(str(item[key])) + 2)
            lens[key] = max_len

        description_space = "    " if description else ""

        # create header
        header_line = second_line = "\n{}".format(description_space)
        for key in header:
            space_no = lens[key] - len(str(header[key]))
            header_line += "{}{}".format(header[key], " " * space_no)
            space_no = lens[key] - len(str(header[key]))
            second_line += "{}{}".format("-" * len(header[key]), " " * space_no)

        # print header
        # bound to 1 line
        # print(header_line[:self._columns] + second_line[:self._columns])

        # multiple lines
        print(header_line.rstrip() + second_line.rstrip())

        for item in list_items:
            line = "    " if description else ""
            for key in item:
                space_no = lens[key] - len(str(item[key]))
                line += "{}{}".format(item[key], " "*space_no)

            # bound to 1 line
            # print(line[:self._columns])

            # print multiple lines
            print(line.rstrip())

    ############################################################################
    #                        Run functions                                     #
    ############################################################################
    def _prepare_module(self, module):
        for option in self._session.options:
            value = self._session.options[option]

            # if the options is a device, check if that device has been added
            if option == "device" and value != None and value:
                value = self._session.devices[int(value)]["device"]

            # if the options is from the results list, get the value
            elif value and str(value).startswith("result:") and \
            str(value).replace("result:", "") in self._session.results:
                value = self._session.results[value.replace("result:", "")]

            if value == None or value == "None" or not value:
                value = ""

            if value and str(value).lower().strip() == "true":
                value = True

            if value and str(value).lower().strip() == "false":
                value = False

            setattr(module, option, value)

    def _print_result(self, result):
        from scrounger.core.module import validate_analysis_result

        if "exceptions" in result:
            for e in result["exceptions"]:
                self._print_error("Exception: {}".format(e.message))

        if "print" in result:
            self._print_status(result.pop("print"))

        for key in result:
            if key.endswith("_result") and validate_analysis_result(
                result[key]):
                print_result = "Analysis result: {} (Severity: {})".format(
                    result[key]["title"], result[key]["severity"])
                print_result = "{}\n    Should Be Reported: {}".format(
                    print_result, "Yes" if result[key]["report"] else "No")

                if "verbose" in self._session.global_options and \
                self._session.global_options["verbose"].lower() == "true":
                    print_result = "{}\n    Details:\n{}".format(
                        print_result, result[key]["details"])

                self._print_status(print_result)

    def do_run(self, args):
        """Runs the current active module"""
        try:
            module = self._session.instance()
            self._prepare_module(module)
            module.validate_options()
            result = module.run()
            self._print_result(result)
            self._session.results.update(result)
        except Exception as e:
            self._print_error("Exception: {}".format(e.message))

            # print debug
            if "debug" in self._session.global_options and \
            self._session.global_options["debug"] == "True":
                import traceback
                print(traceback.format_exc())

    ############################################################################
    #                        Show functions                                    #
    ############################################################################

    def do_print(self, args):
        """Prints the full value of a result, option or global option"""
        name, value = None, "IgnoredValue"

        print_type = args.split(" ", 1)[0]
        if "result" in print_type:
            name = args.split(" ", 1)[-1]
            if name in self._session.results:
                value = self._session.results[name]

        elif "option" in print_type:
            name = args.split(" ", 1)[-1]
            if name in self._session.options:
                value = self._session.options[name]

        elif "global" in print_type:
            name = args.split(" ", 1)[-1]
            if name in self._session.global_options:
                value = self._session.global_options[name]

        if name and value != "IgnoredValue":
            print("\n{} Name: {}".format(print_type.capitalize(), name))
            print("Value: {}".format(value))


    def complete_print(self, text, line, start_index, end_index):
        options = ["option", "result", "global"]

        if "option" in line:
            return [
                option for option in self._session.options
                if option.startswith(text)
            ]

        if "global" in line:
            return [
                option for option in self._session.global_options
                if option.startswith(text)
            ]

        if "result" in line:
            return [
                option for option in self._session.results
                if option.startswith(text)
            ]

        return [option for option in options if option.startswith(text)]

    def do_devices(self, args):
        """Shows the added devices"""

        header = {1: "Scrounger ID", 2: "Device OS", 3: "Identifier"}
        list_items = [
            {
                1: device,
                2: self._session.devices[device]["type"],
                3: self._session.devices[device]["device"].device_id()
            } for device in self._session.devices
        ]

        self._print_list(header, list_items, "Added Devices")

    def do_results(self, options):
        """Shows the saved results"""

        header = {1: "Name", 2: "Value",}
        list_items = [
            {
                1: result,
                2: self._session.results[result]
            } for result in self._session.results
        ]

        self._print_list(header, list_items, "Results")

    def do_show(self, options):
        """Shows options, devices and results"""

        if options.startswith("options"):
            self.do_options(None)

        elif options.startswith("devices"):
            self.do_devices(options.split(" ", 1)[-1])

        elif options.startswith("results"):
            self.do_results(options.split(" ", 1)[-1])


    def complete_show(self, text, line, start_index, end_index):
        options = ["options", "devices", "results"]
        return [option for option in options if option.startswith(text)]

    ############################################################################
    #                      Add device functions                                #
    ############################################################################

    def do_add_device(self, option):
        """Adds an iOS or Android device to the list of devices to use"""
        options = option.split(" ", 2)

        if len(options) < 2 or options[0] != "ios" and options[0] != "android":
            print("Invalid add_device command")

        else:
            if options[0] == "ios":
                from scrounger.core.device import IOSDevice as Device
            elif options[0] == "android":
                from scrounger.core.device import AndroidDevice as Device

            try:
                self._session.devices[max([0] + self._session.devices.keys()) + 1] = {
                    "device": Device(options[1]),
                    "type": options[0]
                }
            except Exception as e:
                self._print_error("Device not found: {}".format(e.message))

    def complete_add_device(self, text, line, start_index, end_index):
        os_types = ["android", "ios"]
        command = "add_device"

        os_type = [option for option in os_types
            if line.startswith("{} {}".format(command, option))]
        os_type = os_type[0] if os_type else None

        if not os_type:
            return [option for option in os_types if option.startswith(text)]

        utils = __import__("scrounger.utils.{}".format(os_type),
            fromlist=["devices"])

        return [option for option in utils.devices() if option.startswith(text)]

    ############################################################################
    #                          Options functions                               #
    ############################################################################

    def do_options(self, args):
        """Shows global options and options for the current module"""
        list_items = [
            {1: item, 2: self._session.global_options[item]}
            for item in self._session.global_options
        ]
        self._print_list({1: "Name", 2: "Value"}, list_items, "Global Options")

        if self._session.module():
            header = {1: "Name", 2: "Required", 3: "Description",
                4: "Current Setting"}

            list_items = [{1: option["name"], 2: option["required"],
                3: option["description"],
                4: self._session.options[option["name"]]}
                for option in self._session.module_options()
            ]

            self._print_list(header, list_items,
                "Module Options ({})".format(self._session.module()))

    ############################################################################
    #                    Use and List module functions                         #
    ############################################################################

    def do_list(self, module_type):
        """Lists all available modules. Modules can also be filtered by
keywords. Examples:
    list ios            - lists all modules for ios
    list misc/android   - lists all misc modules for android
    list nodevice       - lists all modules that don't require a device
    list device         - lists all modules that require a device"""

        list_items = []
        for module in self._session.modules():
            if not module_type or module_type in module \
            or "device" in module_type:

                if module.startswith("custom/"):
                    module_class = __import__("{}".format(
                        module.replace("/", ".")), fromlist=["Module"])
                else:
                    module_class = __import__("scrounger.modules.{}".format(
                        module.replace("/", ".")), fromlist=["Module"])

                if hasattr(module_class, "Module") and \
                hasattr(module_class.Module, "meta"):
                    if "device" in [ option["name"]
                    for option in module_class.Module.options]:
                        module = "{}*".format(module)

                    if module_type and module_type == "device" and \
                    "*" not in module:
                        continue

                    if module_type and module_type == "nodevice" and \
                    "*" in module:
                        continue

                    list_items += [{
                        1: module,
                        2: "{}%".format(module_class.Module.meta["certainty"]),
                        3: module_class.Module.meta["author"],
                        4: module_class.Module.meta["description"]
                    }]

        header = {1: "Module", 2: "Certainty", 3: "Author", 4: "Description"}
        self._print_list(header, list_items)

        print("\n*Requires a device to work.")

    def do_back(self, args):
        """Deactivates the activated module"""
        self.prompt = "\n{}scrounger{} > ".format(Color.UNDERLINE, Color.NORMAL)
        self._session.options = {}
        self._session.back()
        self._session.prompt = self.prompt

    def do_use(self, module):
        """Activates a module to be used"""

        self.prompt = "\n{}scrounger{} {}{}{} > ".format(Color.UNDERLINE,
            Color.NORMAL, Color.RED, module, Color.NORMAL)

        try:
            self._session.use(module)
        except Exception as e:
            self._print_error("{}".format(e.message))
            self.prompt = "\n{}scrounger{} > ".format(
                Color.UNDERLINE, Color.NORMAL)

        self._session.prompt = self.prompt

        self._session.options = {}
        for option in self._session.module_options():
            var_name = option["name"]
            self._session.options[var_name] = option["default"]
            if self._session.options[var_name] == None:
                self._session.options[var_name] = ""
            if var_name in self._session.global_options:
                self._session.options[var_name] = self._session.global_options[var_name]

    def complete_use(self, text, line, start_index, end_index):
        return [
            module for module in self._session.modules()
            if module.startswith(text)
        ]

    ############################################################################
    #                         Session functions                                #
    ############################################################################

    def _create_session(self, name):
        if name:
            session = _Session(name)
            self._sessions += [self._session]
            self._session = session
            self._print_status(
                "Created and switched to session {}".format(name))
            self.prompt = "\n{}scrounger{} > ".format(
                Color.UNDERLINE, Color.NORMAL)
            self._session.prompt = self.prompt

    def _delete_session(self, name):
        new_sessions = [
            session for session in self._sessions
            if name != session.name()
        ]
        if len(self._sessions) == len(new_sessions):
            self._print_error("Session {} not found".format(name))
        else:
            self._sessions = new_sessions
            self._print_status("Session {} deleted".format(name))

    def _list_sessions(self):
        header = {1: "Session Name"}
        session_names = [session.name() for session in self._sessions] + \
                ["{}*".format(self._session.name())]

        list_items = [
            {
                1: session_name
            } for session_name in session_names
        ]

        self._print_list(header, list_items, "Sessions")
        print("\n*Current active session")

    def _switch_session(self, name):
        new_session = [
            session for session in self._sessions
            if session.name() == name
        ]

        if len(new_session) > 0:
            new_session = new_session[0]
            new_sessions = [
                session for session in self._sessions
                if session.name() != name
            ] + [self._session]

            self._sessions = new_sessions
            self._session = new_session

            self._print_status("Session switched to {}".format(name))
            self.prompt = self._session.prompt
        else:
            self._print_error("Could not find session {}".format(name))

    def do_sessions(self, args):
        """Lists available sessions"""
        self._list_sessions()

    def do_session(self, options):
        """Create, delete and switch sessions. Examples:
    session create mysession - creates a new session named mysession
    session delete default   - deletes a session named default
    session list             - lists available sessions
    session switch mysession - switches to a session named mysession
    session mysession        - switches to a session named mysession"""
        if "create " in options:
            self._create_session(options.split("create ", 1)[-1])
        elif "delete " in options:
            self._delete_session(options.split("delete ", 1)[-1])
        elif "list" in options:
            self._list_sessions()
        elif "switch " in options:
            self._switch_session(options.split("switch ", 1)[-1])
        else:
            self._switch_session(options.split(" ", 1)[-1])

    def complete_session(self, text, line, start_index, end_index):
        options = [session.name() for session in self._sessions]
        options += [self._session.name()]
        if line.replace("session ", "").count(" ") == 0:
            options += ["create", "delete", "list", "switch"]

        return [
            option for option in options
            if option.startswith(text)
        ]

    ############################################################################
    #                         Set vars functions                               #
    ############################################################################

    def _set_var(self, options, variable):
        if not " " in variable:
            key = variable.strip()
            value = None
        else:
            key, value = variable.split(" ", 1)

        if value == "None" or value == None:
            value = ""

        if value and value.startswith("~/"):
            value = value.replace("~", _HOME, 1)

        if key == "output":
            from scrounger.utils.general import execute
            execute("mkdir -p {}".format(value))

        if key.lower() == "debug" and value.strip().lower() == "true":
            import logging as _logging
            Log.setLevel(_logging.DEBUG)

        options[key] = value

    def do_unset(self, variable):
        """Sets a variable either module or global"""
        if variable.startswith("global "):
            variable = variable.replace("global ", "")
            self._session.global_options[variable.split(" ", 1)[0]] = ""
        else:
            self._session.options[variable.split(" ", 1)[0]] = ""

    def do_set(self, variable):
        """Sets a variable either module or global"""
        if variable.startswith("global ") or not self._session.module():
            variable = variable.replace("global ", "")
            self._set_var(self._session.global_options, variable)
        else:
            self._set_var(self._session.options, variable)

    def _complete_var_helper(self, text, line):
        CMD_LEN = (3, 4)

        commands = line.split(" ")
        options = []

        if "global" in line:
            CMD_LEN = (4, 5)

        if len(commands) < CMD_LEN[0]: # if setting var name or global
            if "global" not in line:
                options = ["global"]
            options += [option for option in self._session.global_options] + [
                option for option in self._session.options]

        elif len(commands) < CMD_LEN[1]: # if setting value
            options = [""] # add None as 1 of the options
            options += ["result:{}".format(name) for name in self._session.results]

        return [option for option in options if option.startswith(text)]

    def complete_unset(self, text, line, start_index, end_index):
        commands = line.split(" ")

        options = []

        if "global" not in line and len(commands) < 3:
            options = ["global"] + [option for option in self._session.options]

        if len(commands) < 4 and "global" in line:
            options += [option for option in self._session.global_options]

        return [option for option in options if option.startswith(text)]

    def complete_set(self, text, line, start_index, end_index):
        from scrounger.utils.general import execute

        CMD_LEN = (3, 4)

        commands = line.split(" ")
        options = []

        if "global" in line:
            CMD_LEN = (4, 5)

        if len(commands) < CMD_LEN[0]: # if setting var name or global
            if "global" not in line:
                options = ["global"]
            options += [option for option in self._session.global_options] + [
                option for option in self._session.options]

        elif len(commands) < CMD_LEN[1]: # if setting value
            options = [""] # add None as 1 of the options
            options += ["result:{}".format(name) for name in self._session.results]

            # looks in the file system
            if text.startswith("./") or text.startswith("/") or \
            text.startswith("~/"):
                options += [f.replace(_HOME, "~") for f in execute(
                    "ls -d {}*".format(text.replace("~", _HOME))).split("\n")]

        options = list(set(options))
        return [option for option in options if option.startswith(text)]

    ############################################################################
    #                          Exit functions                                  #
    ############################################################################

    def do_exit(self, args):
        """Exits the program."""
        return self.do_quit(args)

    def do_quit(self, args):
        """Exits the program."""
        print("\nQuitting...")
        for device in self._session.devices:
            if self._session.devices[device]["type"] == "ios":
                self._session.devices[device]["device"].clean()

        saved_sessions = [
            session for session in self._sessions
            if session.name() != "default"
        ]
        if self._session.name() != "default":
            saved_sessions += [self._session]
        _save_sessions(saved_sessions, _SESSION_FILE)

        self.postloop()

        raise SystemExit

    def precmd(self, cmd):
        if cmd == "EOF":
            self.do_quit(cmd)

        return cmd

class _SignalHandler(object):

    _prompt = None

    def __init__(self, prompt):
        self._prompt = prompt

    def handle(self, signal, frame):
        # add new line and print the prompt again
        print("\n{}{}".format(
            self._prompt.prompt, readline.get_line_buffer()),end="")

        # needs to flush stdout for some reason
        self._prompt.stdout.flush()
        #self._prompt.emptyline()


def _main():
    prompt = _ScroungerPrompt()

    signal_handler = _SignalHandler(prompt)
    _signal.signal(_signal.SIGINT, signal_handler.handle)

    prompt.prompt = "\n{}scrounger{} > ".format(Color.UNDERLINE, Color.NORMAL)
    prompt.cmdloop("Starting Scrounger console...")

if __name__ == '__main__':
    _main()