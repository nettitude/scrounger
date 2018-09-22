from scrounger.utils.config import Log as _Log
from scrounger.utils.config import binary_memory as _memory

"""
Module with utility functions.
"""

def execute(command):
    """
    Executes a command on the local host.

    :param str command: the command to be executed
    :return: returns the output of the STDOUT or STDERR
    """
    from subprocess import check_output, STDOUT
    command = "{}; exit 0".format(command)

    # log command that is going to be run
    _Log.debug("Shell Command: {}".format(command))

    return check_output(command, stderr=STDOUT, shell=True)

def process(command):
    """
    Executes a command and returns the process

    :param command: the command to be executed
    :return: returns the process off the executed command
    """
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE, stderr=PIPE, shell=True)

def file_exists(file_path):
    """
    Checks if a file exists in the local host.

    :param str file_path: the path to the local file to check
    :return: True if the file exists or False otherwise
    """
    from os import path
    return path.isfile(file_path)

def remove_multiple_spaces(string):
    """
    Strips and removes multiple spaces in a string.

    :param str string: the string to remove the spaces from
    :return: a new string without multiple spaces and stripped
    """
    from re import sub
    return sub(" +", " ", string.strip())

def strings(binary):
    """
    Runs and returns the results of the command strings on a binary file

    :params str binary: the path to the binary
    :return: the raw result of the strings command
    """
    return execute("strings {}".format(binary))

def grep(needle, haystack, grep_options):
    """
    Returns the result of greping for a needle in a haystack

    :param str needle: the needle to look for
    :param str haystack: the haystack to look in
    :param str grep_options: the modifiers to be passed to grep
    :return: the result of the grep command
    """
    return execute("grep {} \"{}\" {} /dev/null".format(
        grep_options, needle, haystack))

def pretty_grep(needle, haystack):
    """
    Returns a well formatted dict with the results of grepping the needle in the
    haystack

    :param str needle: the needle to look for - needs to be a regex
    :param str haystack: the haystack to look in
    :return: a dict ordered by filename with a list of dict containing the
    finding and the line number
    """
    grep_result = grep(needle, haystack, "-arEin")

    findings = {}
    for line in grep_result.split("\n"):

        # if line is blank or if it does not have the right format
        if not line or line.count(":") < 2:
            continue

        filename, line_number, details = line.split(":", 2)

        # creat a new list if filename not in findings
        if filename not in findings:
            findings[filename] = []

        findings[filename].append({
            "line": line_number.strip(),
            "details": details.strip()
        })

    return findings

def pretty_multiline_grep(needle, haystack, no_lines, after=True):
    """
    Returns a well formatted dict with the results of grepping the needle in the
    haystack

    :param str needle: the needle to look for - needs to be a regex
    :param str haystack: the haystack to look in
    :param int no_lines: number of lines to be displayed
    :param Bool after: True if lines to display are after or False if lines to
    display are before
    :return: a dict ordered by filename with a list of dict containing the
    finding and the line number
    """
    additional_modifiers = "-{} {}".format("A" if after else "B", int(no_lines))

    grep_result = grep(needle, haystack, "{} -arEin".format(
        additional_modifiers))

    findings = {}
    for line in grep_result.split("\n"):

        # if line is blank or if it does not have the right format
        if not line or (line.count(":") < 2 and (
            line.count("-") < 2 or len(line) < 5)):
            continue

        if line.count(":") < 2:
            filename, line_number, details = line.split("-", 2)
        else:
            filename, line_number, details = line.split(":", 2)

        # create a new list if filename not in findings
        if filename not in findings:
            findings[filename] = []

        findings[filename].append({
            "line": line_number.strip(),
            "details": details.strip()
        })

    return findings

def pretty_grep_to_str(grep_result, haystack, ignore=None):
    """
    Returns a str containing the grep results without the ignored paths

    :param dict grep_result: the result of a pretty_grep call
    :param str haystack: the base path of the grrp haystack
    :param list ignore: a list of str with paths to be ignored
    :return: a pretty str with the grep results
    """
    if not ignore:
        ignore = []

    final_str = ""
    for filename in grep_result:

        # bypass ignored paths
        if any([ignore_path in filename for ignore_path in ignore]):
            continue

        final_str = "{}\n* {}".format(final_str, filename.replace(haystack, ""))

        # sort the results by line
        for result in sorted(
            grep_result[filename], key=lambda k: int(k["line"])):
            final_str = "{}\n * Line {}: {}".format(final_str, result["line"],
                result["details"])

    return final_str

# ******************************************************************************
# Interactive Process
# ******************************************************************************

class InteractiveProcess(object):
    """
    Class representing an object that interacts with a binary multiple times
    """
    _process = _command = _executable = None

    def __init__(self, command):
        """
        Creates an interactive process to interact with out of a command

        :param str command: the command to be executed
        """

        from fcntl import fcntl, F_GETFL, F_SETFL
        from subprocess import Popen, PIPE
        import os

        self._command = command
        self._executable = command.split(" ", 1)[0]

        _Log.debug("Starting the interactive process: {}".format(command))

        self._process = Popen(command, shell=True, stdout=PIPE, stdin=PIPE,
            stderr=PIPE)
        fcntl(self._process.stdin, F_SETFL,
            fcntl(self._process.stdin, F_GETFL) | os.O_NONBLOCK)
        fcntl(self._process.stdout, F_SETFL,
            fcntl(self._process.stdout, F_GETFL) | os.O_NONBLOCK)

    def write(self, command):
        """
        Writes a command into the interactive process

        :param str command: the command to be sent to the interactive process
        :return: nothing
        """
        import os

        _Log.debug("Sending to process {}: {}".format(
            self._executable, command))

        # add a new line and send the command to the process stdin
        os.write(self._process.stdin.fileno(), "{}\n".format(command))

    def read(self):
        """
        Reads from the process stdout

        :return: a str with the stdout result or None
        """
        import os

        try:
            return self._process.stdout.read()
        except:
            _Log.debug("Nothing to read from {}".format(self._executable))
            # there is nothing to read, return None
            return None

    def kill(self):
        """
        Stops the process - avoid hanging process
        """
        # try to communicate first and then kill
        try:
            self._process.communicate("")
            self._process.kill()
        except:
            # couldn't kill
            pass

# ******************************************************************************
# Requires Decorator
# ******************************************************************************

class OSNotSupportedException(Exception):
    pass

class BinaryNotFoundException(Exception):

    KNOWN_BINARIES = {
        "jtool": "http://www.newosxbook.com/tools/jtool.tar",
        "ldid": "https://github.com/daeken/ldid",
    }

    def __init__(self, message, binary):
        """
        Creates a binary not found exception

        :param str message: the message to be displayed by the error
        :param str binary: the binary that was not found
        """
        super(BinaryNotFoundException, self).__init__(message)
        self.binary = binary

class IOSBinaryNotFoundException(BinaryNotFoundException):
    KNOWN_IOS_BINARY_PACKAGES = {
        "plutil": "com.ericasadun.utilities",
        "appinst": "com.linusyang.appinst",
    }

    BUNDLED_IOS_BINARIES = [
        "clutch", "dump_file_protection", "dump_backup_flag", "dump_keychain",
        "dump_log", "listapps", "gdb"
    ]

class AndroidBinaryNotFoundException(BinaryNotFoundException):
    pass

class UnauthorizedDevice(Exception):
    pass

class requires_unix(object):
    """
    Decorator that checks if the running OS is unix base
    """
    def __call__(self, func):
        def wrapper(obj=None, *args, **kwargs):
            from scrounger.core.device import Host
            SUPPORTED_OS = ["linux", "darwin"]
            host_os = Host().os()
            if host_os not in SUPPORTED_OS:
                raise OSNotSupportedException(
                    "{} not supported.".format(host_os))

            return func() if not obj else func(obj, *args, **kwargs)

        return wrapper

class requires_binary(object):
    """
    Decorator that checks if the required binary is in the path
    """

    def __init__(self, binary):
        """
        Creates a decorator that will check if a binary is in the path

        :param str binary: the binary to verify
        """
        self._binary = binary

    def __call__(self, func):
        def wrapper(obj=None, *args, **kwargs):

            # check if we checked and found the binary before
            if self._binary not in _memory["binary"]:

                # check if binary exists
                binary = execute("command -v {}".format(self._binary))
                if not binary or 'not found' in binary:
                    raise BinaryNotFoundException("{} binary not found.".format(
                        self._binary), self._binary)

                # binary found - add it to the list
                _memory["binary"] += [self._binary]

            return func() if not obj else func(obj, *args, **kwargs)

        return wrapper

class requires_ios_binary(object):
    """
    Decorator that checks if the required binary is in the ios device path
    """

    def __init__(self, device, binary):
        """
        Creates a decorator that will check if a binary is in the ios PATH

        :param str device: the device where the binary is to be found
        :param str binary: the binary to verify
        """
        self._binary = binary
        self._device = device

    def __call__(self, func):
        def wrapper(obj=None, *args, **kwargs):

            # get device id
            device_id = self._device.device_id()
            if device_id not in _memory["ios"]:
                _memory["ios"][device_id] = []

            # check if we checked and found the binary before
            if self._binary not in _memory["ios"][device_id]:

                binary = self._device.execute(
                    "command -v {}".format(self._binary))[0]
                if not binary or 'not found' in binary:
                    raise IOSBinaryNotFoundException(
                        "{} binary not found.".format(self._binary),
                        self._binary)

                # binary found - add it to the list
                _memory["ios"][device_id] += [self._binary]

            return func() if not obj else func(obj, *args, **kwargs)

        return wrapper

class requires_ios_package(object):
    """
    Decorator that checks if the required packages are installed
    """

    def __init__(self, device, package):
        """
        Creates a decorator that will check if a packages is installed

        :param str device: the device where the package is to be found
        :param str package: the package to verify
        """
        self._package = package
        self._device = device

    def __call__(self, func):
        def wrapper(obj=None, *args, **kwargs):

            # get device id
            device_id = self._device.device_id()
            if device_id not in _memory["ios_packages"]:
                _memory["ios_packages"][device_id] = []

            # check if we checked and found the binary before
            if self._package not in _memory["ios_packages"][device_id]:

                packages = self._device.execute("dpkg -l")[0]
                if self._package not in packages:
                    raise Exception("{} not installed.".format(self._package),
                        self._package)

            # binary found - add it to the list
            _memory["ios_packages"][device_id] += [self._package]

            return func() if not obj else func(obj, *args, **kwargs)

        return wrapper

class requires_android_binary(object):
    """
    Decorator that checks if the required binary is in the android path
    """

    def __init__(self, device, binary):
        """
        Creates a decorator that will check if a binary is in the android PATH

        :param str device: the device where the binary is to be found
        :param str binary: the binary to verify
        """
        self._binary = binary
        self._device = device

    def __call__(self, func):
        def wrapper(obj=None, *args, **kwargs):

            # get device id
            device_id = self._device.device_id()
            if device_id not in _memory["android"]:
                _memory["android"][device_id] = []

            # check if we checked and found the binary before
            if self._binary not in _memory["android"][device_id]:
                binary = self._device.execute(
                    "command -v {}".format(self._binary))
                if not binary or 'not found' in binary:
                    raise AndroidBinaryNotFoundException(
                        "{} binary not found.".format(self._binary),
                        self._binary)

            # binary found - add it to the list
            _memory["android"][device_id] += [self._binary]

            return func() if not obj else func(obj, *args, **kwargs)

        return wrapper