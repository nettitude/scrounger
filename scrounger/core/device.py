"""
Device Modules to be used as a connection bridge with ios and android devices
"""

from scrounger.utils.general import requires_binary as _requires_binary
from scrounger.utils.general import requires_ios_binary as _requires_ios_binary
from scrounger.utils.general import requires_ios_package as \
_requires_ios_package
from scrounger.utils.general import requires_android_binary as \
_requires_android_binary
from scrounger.utils.config import Log as _Log

class BaseDevice(object):
    """
    Used for validation purposes only
    """

    def clean(self):
        """
        Cleans up anything left on the device
        """
        pass

class IOSDevice(BaseDevice):
    """
    This class will be used as a bridge between the host and the ios device
    """

    _ssh_session = _iproxy_process = _timer = None

    # **************************************************************************
    # Object helper functions
    # **************************************************************************

    def __init__(self, device_id, username="root", password="alpine"):
        """
        Creates an iOS Device object that allows the user to interact with the
        ios device over ssh

        :param str device_id: the id of the device to connect to
        :param str username: the ssh username to use to connect to the device
        :param str password: the password to use to connect to the device
        """
        self._device_id = device_id
        self._username = username
        self._password = password

    def __str__(self):
        """Returns a string representation of the device"""
        return "iOS Device ({})".format(self.device_id())

    def device_id(self):
        """ Returns the device ID """
        return self._device_id

    @_requires_binary("iproxy")
    def _start_connection(self):
        """
        Starts an SSH connection to the remote device
        """
        from scrounger.utils.ssh import SSHClient
        from scrounger.utils.general import process
        from scrounger.utils.config import SSH_COMMAND_TIMEOUT
        from scrounger.utils.config import SSH_SESSION_TIMEOUT

        # setup
        if not self._ssh_session:
            # this was breaking
            #self._iproxy_process = process(
            #    'iproxy 2222 22 {}'.format(self._device_id))
            self._iproxy_process = process("iproxy 2222 22")
            self._ssh_session = SSHClient("127.0.0.1", 2222,
                self._username, self._password, SSH_COMMAND_TIMEOUT)
            self._ssh_session.connect()

            # Log a new sessions
            _Log.debug("new ssh session started.")

        # start a tiemout for the connection
        from threading import Timer
        if self._timer:
            self._timer.cancel() # cancel old timer and start new one

        self._timer = Timer(SSH_SESSION_TIMEOUT, self._stop_connection)
        self._timer.start()

    def _stop_connection(self):
        """
        Stops the SSH connection with the remote device
        """
        from scrounger.utils.general import execute

        # cleanup
        if self._timer:
            self._timer.cancel()
            self._timer = None

        if self._ssh_session:
            self._ssh_session.disconnect()
            #self._iproxy_process.kill()
            self._iproxy_process = self._ssh_session = None
            execute('killall iproxy') # make sure iproxy is killed

            # Log session stop
            _Log.debug("ssh session killed.")

    def _cat_file(self, file_path):
        """
        Cats a file on the remote device an returns the content

        :param str file_path: the file to be catted
        :return: returns the content of the file
        """
        # prepare file name
        file_path = file_path.replace(" ", "\ ")

        return self.execute("cat {}".format(file_path))[0]

    def _rm_file(self, file_path):
        """
        Deletes a file from the remote device

        :param str file_path: the file to be removed
        :return: returns nothing
        """
        # prepare file name
        file_path = file_path.replace(" ", "\ ")

        self.execute("rm -f {}".format(file_path))

    def clean(self):
        """
        Cleans up the device object when not needed anymore - mainly stops the
        SSH server
        """
        self._stop_connection()

    # **************************************************************************
    # Device functions
    # **************************************************************************

    def execute(self, command):
        """
        Executes a command on the device and returns STDOUT and STDERR

        :param str command: the command to be executed
        :return: returns the STDOUT and STDERR of the executed command
        """

        # start a connection if there is none
        self._start_connection()

        # log command that is going to be run
        _Log.debug("running: {}".format(command))

        # execute
        stdout, stderr = self._ssh_session.execute(command)

        # log result
        #_Log.debug("stdout: {}".format(stdout))
        #_Log.debug("stderr: {}".format(stderr))

        return stdout, stderr

    def get(self, remote_file_path, local_file_path):
        """
        Retrieves a file from the remote device

        :param str remote_file_path: the path on the remote device
        :param str local_file_path: the path on the local host to copy the file
        to (it needs to contain the file name too)
        :return: returns nothing
        """
        from scrounger.utils.general import execute

        # start a connection if there is none
        self._start_connection()

        # logging files
        _Log.debug("copying {} to {}.".format(remote_file_path,
            local_file_path))

        # create local file path if not exists
        execute("mkdir -p {}".format(local_file_path.split("/", 1)[0]))

        # get file
        self._ssh_session.get_file(remote_file_path, local_file_path)

    def put(self, local_file_path, remote_file_path):
        """
        Copies a file to the remote device.

        :param str file_path: the local file path
        :param str remote_file_path: the remote path where to copy the file to
        (it needs to contain the file name too)
        :return: returns nothing
        """
        # start a connection if there is none
        self._start_connection()

        # logging files
        _Log.debug("copying {} to {}.".format(local_file_path,
            remote_file_path))

        # put file
        self._ssh_session.put_file(local_file_path, remote_file_path)

    def plist(self, plist_file_path):
        """
        Returns the contents of a plist file on the remote device

        :param str plist_file_path: the plist file to be read
        :return: returns a dict with the plist contents
        """
        from scrounger.utils.ios import plist
        from scrounger.utils.general import execute

        # get local file
        local_file = "/tmp/Info.plist"
        self.get(plist_file_path, local_file)
        plist_content = plist(local_file)

        # clean up tmp file
        execute("rm -rf {}".format(local_file))

        return plist_content

        """
        file_content = self._cat_file(plist_file_path)

        # clean up broken chars (hacky bit)
        cleaned_file_content = ""
        for char in file_content:
            if ord(char) < 32 and ord(char) != 9 and ord(char) != 10:
                char = " "
            cleaned_file_content += char

        return plist_to_dict(cleaned_file_content)
        """

    def system_version(self):
        """
        Retrieves the iOS version installed on the device

        :return: returns a string with the iOS version
        """
        @_requires_ios_binary(self, "grep")
        def _system_version(self):
            os_version_file = "/System/Library/CoreServices/SystemVersion.plist"
            version = self.execute("grep -A 1 ProductVersion {}".format(
                os_version_file))[0] # stdout

            import re
            return re.search(r"[\d.]+", version).group()

        return self._system_version()

    def apps(self):
        """
        Gets the apps installed in the device and their paths

        :return: returns a dict with the installed apps and their info
        """
        @_requires_ios_binary(self, "ipainstaller")
        def _apps():
            apps = {}

            app_ids = self.execute("ipainstaller -l")[0].split("\n")[:-1]
            for app in app_ids:
                app_info = self.execute("ipainstaller -i {}".format(app))[0]
                apps[app] = {}
                for info in app_info.split("\n")[:-1]:
                    key, value = info.split(":", 1)
                    apps[app][key.strip().lower().replace(
                        " ", "_")] = value.strip()

            return apps

        return _apps()

    def install_binary(self, local_path):
        """
        Installs a binary application on the remote device under /usr/bin

        :param str local_path: the local binary to install on the device
        :return: returns True if succesful or False if not
        """
        install_path = "/usr/bin/{}".format(local_path.rsplit("/", 1)[-1])

        self.put(local_path, install_path)

        # make it executable
        self.execute("chmod 755 {}".format(install_path))

        return "No such file" not in self.execute(
            "ls {}".format(install_path))[1]

    def logs(self, app_binary_name=""):
        """
        Dumps logs from the remote device. If an app_id is provided only dumps
        logs from the provided app

        :param str app_binary_name: the app binary name to dump lgos from
        :return: logs from all the apps or the specified app
        """
        @_requires_ios_binary(self, "dump_log")
        def _logs(app_binary_name=""):
            # prepare filename
            app_binary_name = app_binary_name.replace(" " , "\ ")
            return self.execute("dump_log {}".format(app_binary_name))[0]

        return _logs(app_binary_name)

    def backup_flag(self, file_path):
        """
        Dumps the backup flag from the desired file on the remote device

        :param str file_path: the path of the file on the remote device to dump
        the backup flag from
        :return: returns the backup flag
        """
        @_requires_ios_binary(self, "dump_backup_flag")
        def _backup_flag(file_path):
            # prepare filename
            file_path = file_path.replace(" " , "\ ")
            return self.execute("dump_backup_flag {}".format(file_path))[0][:-1]

        return _backup_flag(file_path)

    def file_protection(self, file_path):
        """
        Dumps the file protection flags from the desired file on the remote
        device

        :param str file_path: the path of the file on the remote device to dump
        the file protection flag from
        :return: returns the file protection flag
        """
        @_requires_ios_binary(self, "dump_file_protection")
        def _file_protection(file_path):
            # prepare filename
            file_path = file_path.replace(" " , "\ ")
            return self.execute(
                "dump_file_protection {}".format(file_path))[0][:-1]

        return _file_protection(file_path)

    def keychain_data(self):
        """
        Dumps all keychain data on the remote device

        :return: a dict with the keys and values on the keychain
        """
        @_requires_ios_binary(self, "dump_keychain")
        def _keychain_data():
            tmp_keychain_folder = "/tmp/scrounger-keychain"

            # prepare to dump keychain data
            self.execute("mkdir {}".format(tmp_keychain_folder))

            # dump keychain data
            self.execute("cd {}; dump_keychain".format(tmp_keychain_folder))

            # get and parse result
            keychain = self.plist("{}/keys.plist".format(tmp_keychain_folder))
            keychain += self.plist("{}/genp.plist".format(tmp_keychain_folder))
            keychain += self.plist("{}/cert.plist".format(tmp_keychain_folder))
            keychain += self.plist("{}/inet.plist".format(tmp_keychain_folder))

            # cleanup
            self.execute("rm -rf {}".format(tmp_keychain_folder))

            return keychain

        return _keychain_data()

    def install(self, ipa_file_path):
        """
        Installs an IPA app on the remote device

        :param str ipa_file_path: the IPA file on the remote device to install
        :return: the result of installing the app
        """

        @_requires_ios_binary(self, "ipainstaller")
        @_requires_ios_package(self, "net.angelxwind.appsyncunified")
        def _install(ipa_file_path):
            # prepare filename
            ipa_file_path = ipa_file_path.replace(" " , "\ ")

            result = self.execute(
                "ipainstaller -f -d {}".format(ipa_file_path))[0]

            # update app list
            self.execute("uicache")

            return result

        return _install(ipa_file_path)

    def find_files(self, paths):
        """
        Returns a list of files in the selecged paths

        :param str paths: the root paths to start looking for files from - these
        can be seperated by space for multiple file paths
        :return: list with the found files
        """
        @_requires_ios_binary(self, "find")
        def _find_files(paths):
            return self.execute("find {} -type f".format(paths))[0].split("\n")

        return _find_files(paths)

    # **************************************************************************
    # Applications functions
    # **************************************************************************

    def start(self, binary_path):
        """
        Starts an application on the connected device

        :param str binary_path: the application to start
        :return: the result of opening the app
        """
        @_requires_ios_binary(self, "open")
        def _start(binary_path):
            return self.execute("open {}".format(binary_path))

        return _start(binary_path)

    def pull_data_contents(self, data_path, local_path):
        """
        Gets an application's data from the device to a local path

        :param str data_path: the path to the application's data
        :param str local_path: the destination path
        :return: nothing
        """

        @_requires_ios_binary(self, "find")
        def _pull_data_contents(data_path, local_path):
            #from scrounger.utils.general import execute

            data_files = self.execute("find {} -type f".format(data_path))[0]
            for data_file in data_files.split("\n"):
                local_file_path = "{}{}".format(local_path,
                    data_file.replace(data_path, ""))

                # NO NEED TO DO IT - get is now responsible for it
                # create destination folders if they don't exist
                #execute("mkdir -p {}".format(
                #    local_file_path.rsplit("/", 1)[0]))

                # copy files
                self.get(data_file, local_file_path)

        return _pull_data_contents(data_path, local_path)

    def otool(self, options, app_binary_path):
        """
        Executes otool on the device

        :param str options: the options to pass to otool with `-` attached
        :param str app_binary_path: the binary to run otool on
        :return: otool result stdout and stderr
        """
        @_requires_ios_binary(self, "otool")
        def _otool(options, app_binary_path):
            app_binary_path = app_binary_path.replace(" " , "\ ")
            return self.execute("otool {} {}".format(options, app_binary_path))

        return _otool(options, app_binary_path)

    def ldid(self, options, app_binary_path):
        """
        Executes ldid on the device

        :param str options: the options to pass to ldid with `-` attached
        :param str app_binary_path: the binary to run ldid on
        :return: otool ldid stdout and stderr
        """
        @_requires_ios_binary(self, "ldid")
        def _ldid(options, app_binary_path):
            app_binary_path = app_binary_path.replace(" " , "\ ")
            return self.execute("ldid {} {}".format(options, app_binary_path))

        return _ldid(options, app_binary_path)

    def decrypt_binary(self, app_id):
        """
        Decrypt the binary of the application only

        :param str app_id: the application identifier of the app to decrypt
        :return: returns the remote path where the application was decrypted to
        or None if it failed
        """
        output = self._decrypt_app_helper(app_id, "-b")

        if "Finished dumping" in output:
            return "{}/{}".format(output.rsplit(" to ", 1)[1].split("\n")[0],
                app_id)

        return None

    def decrypt(self, app_id):
        """
        Decrypt the binary of the application and packs the application into
        an ipa file

        :param str app_id: the application identifier of the app to decrypt
        :return: returns the remote path where the application was packed into
        or None if it failed
        """
        output = self._decrypt_app_helper(app_id, "-d")

        if "DONE: " in output:
            return output.split("DONE: ", 1)[1].split("\n")[0]

        return None

    def _decrypt_app_helper(self, app_id, decrypt_type):
        """
        Decrypts an app and returns the result output

        :param str app_id: the id of the app to be decrypted
        :param str decrypt_type: the type of decryption to be done - either
        binary only (-b) or packed into ipa (-d)
        :return: returns the output of the decryption
        """
        @_requires_ios_binary(self, "clutch")
        def __decrypt_app_helper(app_id, decrypt_type):
            from socket import timeout
            scrounger_clutch_log_file = "/tmp/scrounger-clutch.log"

            try:
                output = self.execute("clutch -n {} {} &> {}".format(
                    decrypt_type, app_id, scrounger_clutch_log_file))[0]
            except timeout:
                _Log.debug("ssh command timedout.")

            output = self._cat_file(scrounger_clutch_log_file)

            # cleanup log file
            self._rm_file(scrounger_clutch_log_file)

            return output

        return __decrypt_app_helper(app_id, decrypt_type)


from scrounger.utils.android import _adb_command

class AndroidDevice(BaseDevice):
    """
    This class will be used as a bridge between the host and the android device
    """

    _device_id = None

    def __init__(self, device_id):
        """
        Creates an object that will be a wrapper to interact with the android
        device. It also checks if the device trusts the host.
        """
        from scrounger.utils.android import devices
        from scrounger.utils.general import UnauthorizedDevice

        self._device_id = device_id

        devices_list = devices()
        if self._device_id not in devices_list or\
            devices_list[self._device_id] == "unauthorized":
            raise UnauthorizedDevice(
                "The device {} does not trust this host.".format(
                    self._device_id))

    def __str__(self):
        """Returns a string representation of the device"""
        return "Android Device ({})".format(self.device_id())

    def device_id(self):
        """ Returns the device ID """
        return self._device_id

    def execute(self, command):
        """
        Executes a command on the target device

        :param str command: the command to be executed
        :return: stdout and stderr of the executed command
        """
        return _adb_command("-s {} shell {}".format(self._device_id, command))

    def root_execute(self, command):
        """
        Executes a command on the target device as root

        :param str command: the command to execute
        :return: stdout and stderr from the executed command
        """
        return self.execute("su -c '{}'".format(command.replace("'", "\'")))

    def install(self, apk_path):
        """
        Installs an application in a target device

        :param str apk_path: the apk local file path
        :return: nothing
        """
        _adb_command("-s {} install {}".format(self._device_id, apk_path))

    def uninstall(self, package):
        """
        Uninstalls an application from a target device

        :param str package: the package to be uninstalled
        :return: nothing
        """
        _adb_command("-s {} uninstall {}".format(self._device_id, package))

    def get(self, remote_file_path, local_file_path):
        """
        Pulls a file from a target device

        :param str remote_file_path: the file to be retrieved
        :param str local_file_path: the local filepath where to copy the file to
        :return: nothing
        """
        _adb_command("-s {} pull {} {}".format(self._device_id,
        remote_file_path, local_file_path))

    def put(self, local_file_path, remote_file_path):
        """
        Pushes a file to a target device

        :param str local_file_path: the file to be copied into the device
        :param str remote_file_path: the remote filepath to copy the file to
        :return: nothing
        """
        _adb_command("-s {} push {} {}".format(self._device_id,
            local_file_path, remote_file_path))

    def connected(self):
        """
        Checks if the device is connected

        :return: True if the device is connected and False if not
        """
        from scrounger.utils.android import devices
        return self._device_id in devices()

    def list(self, remote_path):
        """
        Lists all files in a given path on the target device

        :param str remote_path: the path to list files from
        :return: a list of files and folders
        """
        return [listed_file for listed_file in self.execute(
            "ls {}".format(remote_path)).split("\n")]

    def processes(self):
        """
        Returns a list of running processes, their users and pids

        :return: a list of dicts of processes
        """
        @_requires_android_binary(self, "ps")
        def _processes():
            from scrounger.utils.general import remove_multiple_spaces

            processes = []
            for process in self.root_execute("ps").split("\n"):
                if not process: continue
                user = process.split(" ", 1)[0]
                name = process.strip().rsplit(" ", 1)[-1]
                pid  = remove_multiple_spaces(process).split(" ", 2)[1]
                processes += [{"name": name, "user": user, "pid": pid}]

            return processes

        return _processes()

    def packages(self):
        """
        Returns a list of installed apps on target device and their apk paths

        :return: a dict of installed packages and their apk paths
        """
        @_requires_android_binary(self, "pm")
        def _packages():
            packages = {}
            for package in self.execute("pm list packages -f").split("\n"):
                package_name = package.split("=", 1)[-1].strip()
                package_apk  = package.split("=", 1)[0].split(":", 1)[-1].strip()
                packages[package_name] = package_apk

            return packages

        return _packages()

    def apps(self):
        """
        Returns a list of installed apps on target device (just a wrapper for
        packages)

        :return: a dict of installed packages and their apk paths
        """
        return self.packages()

    def start(self, package):
        """
        Starts an application on target device

        :param str package: the application to start
        :return: nothing
        """
        @_requires_android_binary(self, "monkey")
        def _start(package):
            self.execute(
                "monkey -p {} -c android.intent.category.LAUNCHER 1".format(
                    package))

        return _start(package)

    def installed(self, package):
        """
        Checks if an application is installed on the target device

        :param str package: the application identifier
        :return: True if installed or False otherwise
        """
        return package in self.apps()

    def unlocked(self):
        """
        Checks if the target device is unlocked

        :return: True if the target device is unlocked False if not
        """
        @_requires_android_binary(self, "dumpsys")
        @_requires_android_binary(self, "grep")
        def _unlocked():
            from time import sleep
            system_props = ""

            # while it's locked
            while "mHolding" not in system_props:
                sleep(3) # sleep for 3 seconds and try again
                system_props = self.execute(
                    "dumpsys power | grep mHoldingDisplaySuspendBlocker")

            return all("true" in prop.split(
                "=", 1)[-1] for prop in system_props.split("\n")[:-1])

        return _unlocked()

    def data_paths(self, package):
        """
        Returns a list with paths containing application's data

        :param str package: the application identifier
        :return: a list with application's data paths
        """
        return [
            "/data/data/{}".format(package),
            "/data/user/0/{}".format(package)
        ]

    def pull_data_contents(self, package, temp_path, local_path):
        """
        Pulls the data contants generated by the target app

        :param str package: the target app
        :param str temp_path: the folder to temp use to pull contents
        :param str local_path: the path to pull the contents to
        :return: nothing
        """
        target_paths = self.data_paths(package)
        temp_path = "{}/{}".format(temp_path, package)

        # create temp folder
        self.execute("mkdir -p {}".format(temp_path))

        # copy files to temp folder
        for index, target_path in enumerate(target_paths):
            self.root_execute("cp -r {} {}/{}".format(
                target_path, temp_path, index))

        # pull data
        self.get(temp_path, local_path)

        # clean up - to be done by caller
        # self.root_execute("rm -rf {}".format(temp_path))

    def pull_apk(self, package, temp_path, local_path):
        """
        Pulls the data contants generated by the target app

        :param str package: the target app
        :param str temp_path: the folder to temp use to pull the apk
        :param str local_path: the path to pull the apk to
        :return: nothing
        """

        packages = self.packages()
        if package in packages:
            apk_path = packages[package]

        # create temp folder
        self.execute("mkdir -p {}".format(temp_path))

        dest_apk_path = "{}/{}.apk".format(temp_path, package)

        # copy apk to temp folder
        self.root_execute("cp {} {}".format(apk_path, dest_apk_path))

        # pull apk
        self.get(dest_apk_path, local_path)

    def query_provider(self, provider, projection="", selection=""):
        """
        Queries a provider on the target device with optional projections and
        selections

        :param str provider: the provider to query
        :param str projection: the projection to return - double quotes are not
        valid options - this also needs to be double escaped
        :param str selection: the where clause - similar to projection double
        quotes are not a valid options and make sure to double escape
        :return: the result of the query
        """

        if "\"" in projection or "\"" in selection:
            raise Exception("Cannot query providers with double quotes in \
projections or selections.")

        # build query
        query = "content query --uri \\\"content://{}\\\"".format(provider)

        if projection:
            query += " --projection \\\"{}\\\"".format(projection)

        if selection:
            query += " --where \\\"{}\\\"".format(selection)

        return self.root_execute("\"{}\"".format(query))

    def read_provider(self, provider, path=""):
        """
        Reads information from a provider with an option path

        :param str provider: the provider to read from
        :param str path: the optional path to append to the provider
        :return: the result from the read provider
        """
        query = "contant read --uri \\\"content://{}{}\\\"".format(
            provider, path)
        return self.root_execute("\"{}\"".format(query))

    def world_files(self, remote_path, permissions):
        """
        Finds all world files with specified world permission in a path

        :param str remote_path: the path on the target to start looking from
        :param str permissions: the required permissions: rwx, x, rx, rw, etc.
        :return: a list of files found
        """
        files = self.find_files(remote_path)

        perm_files = []
        for file in files:
            file_perms = self.root_execute(
                "ls -la {}".format(file)).strip().split(" ", 1)[0][-3:]
            if all(permission in file_perms for permission in permissions):
                perm_files += [file.strip().rsplit(" ", 1)[-1]]

        return perm_files

    def find_files(self, remote_path):
        """
        Finds all files in a path

        :param str remote_path: the path to start looking from
        :return: a list of files
        """
        @_requires_android_binary(self, "find")
        def _find_files(remote_path):
            find = "find {} -type b -o -type c -o -type f -o -type s".format(
                remote_path)
            return [
                file for file in
                self.root_execute(find).replace("\r\n", "").split("\n")
                if "Permission denied" not in file
            ]

        return _find_files(remote_path)

    def file_content(self, file_path):
        """
        Returns the contents of a given file on the remote device

        :param str file_path: the path to the file to get the contents from
        :return: the contents of the file
        """

        return self.root_execute("cat {}".format(file_path))


class Host(object):
    """
    An object that represents the host where the tool is being executed from
    """

    def os(self):
        """ Returns the type of OS it is running from """
        from platform import system
        return system().lower()
