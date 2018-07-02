#! /usr/bin/env python
from __future__ import print_function
from cmd import Cmd as _Cmd
import signal as _signal

# custom module imports
from sys import path as _path

# scrounger imports
from scrounger.utils.config import _SCROUNGER_HOME, _HISTORY_FILE, _MAX_HISTORY

# change delimters for CMD
import readline


class Color():
    RED = "\033[31m"
    GREEN = "\033[32m"
    NORMAL = "\033[0m"
    UNDERLINE = "\033[4m"

class _ScroungerPrompt(_Cmd, object):
    # TODO: add sessions using the core.session object

    _available_modules = []
    _custom_modules = []
    _options = {}
    _global_options = {
        "device": "",
        "output": "/tmp/scrounger-app"
    }
    _module = _module_class = _rows = _columns = None
    _devices = {}
    _results = {}

    def default(self, line):
        print("{}: command not found".format(line))

    def preloop(self):
        from os import popen, path
        from scrounger.utils.general import execute
        import scrounger.modules

        _Cmd.preloop(self)   ## sets up command completion

        self._rows, self._columns = popen('stty size', 'r').read().split()
        self._rows, self._columns = int(self._rows), int(self._columns)
        if self._columns < 128: self._columns = 128

        # need to add / to then replace it
        modules_path = "{}/".format(scrounger.modules.__path__[0])
        modules = execute("find {} -name '*.py'".format(modules_path))

        self._available_modules = [
            module.replace(modules_path, "").replace(".py", "")
            for module in modules.split("\n")
            if module and "__" not in module
        ]

        # fix for macos
        self._available_modules = [
            module[1:] if module.startswith("/") else module
            for module in sorted(self._available_modules)
        ]

        # add custom modules
        modules_path = "{}/modules/".format(_SCROUNGER_HOME)
        modules = execute("find {} -name \"*.py\"".format(modules_path))

        # add path to sys.path
        _path.append(modules_path)

        #self._custom_modules = [
        self._available_modules += [
            module.replace(modules_path, "").replace(".py", "")
            for module in modules.split("\n")
            if module and "__" not in module
        ]

        execute("mkdir -p {}".format(self._global_options["output"]))

        readline.set_completer_delims(' \t\n')
        if path.exists(_HISTORY_FILE):
            readline.read_history_file(_HISTORY_FILE)

    def postloop(self):
        _Cmd.postloop(self)   ## Clean up command completion

        readline.set_history_length(_MAX_HISTORY)
        readline.write_history_file(_HISTORY_FILE)


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
        for option in self._options:
            value = self._options[option]

            # if the options is a device, check if that device has been added
            if option == "device" and value != None and value:
                value = self._devices[int(value)]["device"]

            # if the options is from the results list, get the value
            elif value and str(value).startswith("result:") and \
            str(value).replace("result:", "") in self._results:
                value = self._results[value.replace("result:", "")]

            if value == None or value == "None" or not value:
                value = ""

            setattr(module, option, value)

    # TODO: needs to be re-written
    def _print_result(self, result):
        from scrounger.core.module import validate_analysis_result

        if "exceptions" in result:
            for e in result["exceptions"]:
                print("[-] {}".format(e))

        if "print" in result:
            print("[+] {}".format(result.pop("print")))

        for key in result:
            if key.endswith("_result") and validate_analysis_result(
                result[key]):
                print("[+] Analysis result:")
                print(result[key]["title"])
                print("    Report: {}".format(result[key]["report"]))
                print("    Details:\n{}".format(result[key]["details"]))

    # TODO: needs to be re-written
    def do_run(self, args):
        """Runs the current active module"""
        try:
            module = self._module_instance
            self._prepare_module(module)
            module.validate_options()
            result = module.run()
            self._print_result(result)
            self._results.update(result)
        except Exception as e:
            print("[-] {}".format(e))

            # print debug
            if "debug" in self._global_options and \
            self._global_options["debug"] == "True":
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
            if name in self._results:
                value = self._results[name]

        elif "option" in print_type:
            name = args.split(" ", 1)[-1]
            if name in self._options:
                value = self._options[name]

        elif "global" in print_type:
            name = args.split(" ", 1)[-1]
            if name in self._global_options:
                value = self._global_options[name]

        if name and value != "IgnoredValue":
            print("\n{} Name: {}".format(print_type.capitalize(), name))
            print("Value: {}".format(value))


    def complete_print(self, text, line, start_index, end_index):
        options = ["option", "result", "global"]

        if "option" in line:
            return [
                option for option in self._options
                if option.startswith(text)
            ]

        if "global" in line:
            return [
                option for option in self._global_options
                if option.startswith(text)
            ]

        if "result" in line:
            return [
                option for option in self._results
                if option.startswith(text)
            ]

        return [option for option in options if option.startswith(text)]

    def do_devices(self, args):
        """Shows the added devices"""

        header = {1: "Scrounger ID", 2: "Device OS", 3: "Identifier"}
        list_items = [
            {
                1: device,
                2: self._devices[device]["type"],
                3: self._devices[device]["device"].device_id()
            } for device in self._devices
        ]

        self._print_list(header, list_items, "Added Devices")

    def do_results(self, options):
        """Shows the saved results"""

        header = {1: "Name", 2: "Value",}
        list_items = [
            {
                1: result,
                2: self._results[result]
            } for result in self._results
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
                self._devices[max([0] + self._devices.keys()) + 1] ={
                    "device": Device(options[1]),
                    "type": options[0]
                }
            except Exception as e:
                print("[-] {}".format(e))

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
            {1: item, 2: self._global_options[item]}
            for item in self._global_options
        ]
        self._print_list({1: "Name", 2: "Value"}, list_items, "Global Options")

        if self._module:
            header = {1: "Name", 2: "Required", 3: "Description",
                4: "Current Setting"}

            list_items = [{1: option["name"], 2: option["required"],
                3: option["description"], 4: self._options[option["name"]]}
                for option in self._module_instance.options
            ]
            self._print_list(header, list_items,
                "Module Options ({})".format(self._module))

    ############################################################################
    #                    Use and List module functions                         #
    ############################################################################

    def do_list(self, module_type):
        """Lists all available modules"""

        list_items = []
        for module in self._available_modules:
            if not module_type or module_type in module:

                if module.startswith("custom/"):
                    module_class = __import__("{}".format(
                        module.replace("/", ".")), fromlist=["Module"])
                else:
                    module_class = __import__("scrounger.modules.{}".format(
                        module.replace("/", ".")), fromlist=["Module"])

                if hasattr(module_class, "Module") and \
                hasattr(module_class.Module, "meta"):
                    list_items += [{
                        1: module,
                        2: "{}%".format(module_class.Module.meta["certainty"]),
                        3: module_class.Module.meta["author"],
                        4: module_class.Module.meta["description"]
                    }]

        header = {1: "Module", 2: "Certainty", 3: "Author", 4: "Description"}
        self._print_list(header, list_items)

    def do_back(self, args):
        """Deactivates the activated module"""
        self.prompt = "\n{}scrounger{} > ".format(Color.UNDERLINE, Color.NORMAL)
        self._options = {}
        self._module = None
        self._module_class = None
        self._module_instance = None

    def do_use(self, module):
        """Activates a module to be used"""

        self._module = module
        self.prompt = "\n{}scrounger{} {}{}{} > ".format(Color.UNDERLINE,
            Color.NORMAL, Color.RED, self._module, Color.NORMAL)


        if module.startswith("custom/"):
            self._module_class = __import__("{}".format(
                module.replace("/", ".")), fromlist=["Module"])
        else:
            self._module_class = __import__("scrounger.modules.{}".format(
                module.replace("/", ".")), fromlist=["Module"])

        self._module_instance = self._module_class.Module()

        if not hasattr(self._module_class, "Module") or not hasattr(
            self._module_class.Module, "meta") or not hasattr(
            self._module_instance, "options"):
            print("[-] Missing required variables or `Module` class")

        self._options = {}
        for option in self._module_instance.options:
            var_name = option["name"]
            self._options[var_name] = option["default"]
            if self._options[var_name] == None:
                self._options[var_name] = ""
            if var_name in self._global_options:
                self._options[var_name] = self._global_options[var_name]

    def complete_use(self, text, line, start_index, end_index):
        return [
            module for module in self._available_modules
            if module.startswith(text)
        ]

    ############################################################################
    #                         Set vars functions                               #
    ############################################################################

    def _set_var(self, options, variable):
        key, value = variable.split(" ", 1)
        if value == "None" or value == None:
            value = ""

        if key == "output":
            from scrounger.utils.general import execute
            execute("mkdir -p {}".format(value))

        options[key] = value

    def do_unset(self, variable):
        """Sets a variable either module or global"""
        if variable.startswith("global "):
            variable = variable.replace("global ", "")
            self._global_options[variable.split(" ", 1)[0]] = ""
        else:
            self._options[variable.split(" ", 1)[0]] = ""

    def do_set(self, variable):
        """Sets a variable either module or global"""
        if variable.startswith("global "):
            variable = variable.replace("global ", "")
            self._set_var(self._global_options, variable)
        else:
            self._set_var(self._options, variable)

    def _complete_var_helper(self, text, line):
        CMD_LEN = (3, 4)

        commands = line.split(" ")
        options = []

        if "global" in line:
            CMD_LEN = (4, 5)

        if len(commands) < CMD_LEN[0]: # if setting var name or global
            if "global" not in line:
                options = ["global"]
            options += [option for option in self._global_options] + [
                option for option in self._options]

        elif len(commands) < CMD_LEN[1]: # if setting value
            options = [""] # add None as 1 of the options
            options += ["result:{}".format(name) for name in self._results]

        return [option for option in options if option.startswith(text)]

    def complete_unset(self, text, line, start_index, end_index):
        commands = line.split(" ")

        options = []

        if "global" not in line and len(commands) < 3:
            options = ["global"] + [option for option in self._options]

        if len(commands) < 4 and "global" in line:
            options += [option for option in self._global_options]

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
            options += [option for option in self._global_options] + [
                option for option in self._options]

        elif len(commands) < CMD_LEN[1]: # if setting value
            options = [""] # add None as 1 of the options
            options += ["result:{}".format(name) for name in self._results]

            # looks in the file system
            if text.startswith("./") or text.startswith("/"):
                options += [f for f in execute(
                    "ls -d {}*".format(text)).split("\n")]

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
        for device in self._devices:
            if self._devices[device]["type"] == "ios":
                self._devices[device]["device"].clean()

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