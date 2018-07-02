"""
Module with android utility functions.
"""

from scrounger.utils.general import requires_binary
from scrounger.utils.general import execute as _execute

@requires_binary("adb")
def _adb_command(command):
    """
    Runs an adb command on the host

    :param str command: the adb command to run
    :return: stdout and stderr from the executed command
    """
    return _execute("adb {}".format(command)).replace("\r\n", "\n")

def devices():
    """
    Returns a list of devices connected to the host

    :return: a list of devices
    """
    device_lines = _adb_command("devices").split("\n")[1:-2]
    devices = {}

    for device in device_lines:
        if device:
            device_id, device_status = device.strip().split("\t", 1)
            devices[device_id] = device_status

    return devices

def avds():
    """
    Returns a list of the installed AVDs

    :return: a list of installed avds
    """
    @requires_binary("avdmanager")
    @requires_binary("grep")
    def _avds():
        avds_raw = _execute("avdmanager list avd | grep Name:")
        return [avd.strip.split(": ", 1)[-1] for avd in avds_raw.split("\n")]

    return _avds()

def decompile(apk_path, destination_path):
    """
    Decompiles an apk file using apktool

    :param str apk_path: the path to the apk file
    :param str destination_path: the destination directory where to decompile
    the application to
    :return: stdout and stderr for debugging
    """
    @requires_binary("apktool")
    def _decompile(apk_path, destination_path):
        return _execute("apktool -q d -f {} -o {}".format(apk_path,
            destination_path))

    return _decompile(apk_path, destination_path)

def recompile(decompiled_app_path, apk_file_path):
    """
    Recompiles a decompiled app using apktool to a new apk file

    :param str decompiled_app_path: the path to the decompiled app
    :param str apk_file_path: the resulting apk file path and filename
    :return: stdout and stderr for debugging
    """
    @requires_binary("apktool")
    def _recompile(decompiled_app_path, apk_file_path):
        return _execute("apktool b -o {} {}".format(apk_file_path,
            decompiled_app_path))

    return _recompile(decompiled_app_path, apk_file_path)

def sign(apk_file_path, signed_apk_file_path, signjar, certificate, pk8):
    """
    Signs an apk file given a certificate, a pk8 file the signapk jar

    :param str apk_file_path: the apk file to be signed
    :param str signed_apk_file_path: the apk file result
    :param str signjar: the signapk.jar file to use for the signing
    :param str certificate: the certificate used to sign the apk file
    :param str pk8: the pk8 key file to use to sign the apk file
    :return: nothing
    """
    @requires_binary("java")
    def _sign(apk_file_path, signjar, certificate, pk8):
        return _execute("java -jar {} {} {} {} {}".format(signjar, certificate, pk8,
            apk_file_path, signed_apk_file_path))

    return _sign(apk_file_path, signjar, certificate, pk8)

def jar(apk_path, jar_file_path):
    """
    Extracts a jar file from an apk file

    :param str apk_path: the path to the apk file
    :param str jar_file_path: the path and name of the resulting jar file
    :return: nothing
    """
    @requires_binary("d2j-dex2jar")
    def _jar(apk_path, jar_file_path):
        _execute("d2j-dex2jar --force -o {} {}".format(jar_file_path, apk_path))

    _jar(apk_path, jar_file_path)

def source(jar_file_path, destination_path):
    """
    Decompiles a jar file into java classes using jd-cli - make sure it is in
    your path

    :param str jar_file_path: the path to the jar to be decompiled
    :param str destination_path: the directory to decompile the jar to
    :return: nothing
    """
    @requires_binary("jd-cli")
    def _source(jar_file_path, destination_path):
        _execute("jd-cli {} -od {}".format(jar_file_path, destination_path))

    return _source(jar_file_path, destination_path)

def extract_providers(decompiled_app_path):
    """
    Extracts provider paths from a decompiled app directory using grep

    :param str decompiled_app_path: the directory where to look for the
    providers
    :return: a sorted list of proviers
    """
    from scrounger.utils.general import pretty_grep
    import re

    providers_regex = r"content://[a-zA-Z0-1.-@/]+"
    providers = []

    grep_result = pretty_grep(providers_regex, decompiled_app_path)

    for filename in grep_result:
        for finding in grep_result[filename]:
            # needs regex search since grep returns the whole line
            provider_path = re.search(providers_regex,
                finding["details"]).group().split("://", 1)[-1].strip()

            # make sure that every provider follows a standard and has no /
            # in the end
            if provider_path.endswith("/"):
                provider_path = provider_path[:-1]

            # TODO: translate @string to value
            providers.append(provider_path)

    # creates a set to make sure there are no duplicates and returns a sorted
    # list
    return sorted(set(providers))

def smali_dirs(decompiled_apk_path):
    """
    Returns a list of directories contianing smali code

    :param str decompiled_apk_path: the path to the decompiled apk directory
    :return: a list with smali directories or an empty list if no smali dir
    """

    dirs = _execute("ls -d {}/smali*".format(decompiled_apk_path))

    if "No such file or directory" in dirs:
        return []

    return [directory.replace(decompiled_apk_path, "")[1:] for directory in
    dirs.split("\n") if directory]

def extract_smali_method(method_name, smali_file):
    """
    Extracts a smali method from a smali file

    :param str method_name: the method to be extracted
    :param str smali_file: the file to extract the method from
    :return: the extracted method or empty string if not found
    """
    with open(smali_file, "r") as fd:
        smali_code = fd.read()

    smali_method = ""
    for line in smali_code.split("\n"):
        # if method has been found and end is in line
        if smali_method and ".end method" in line:
            return smali_method

        # if method has been found then start saving
        elif ".method" in line and method_name in line and not smali_method:
            smali_method = line

        elif smali_method:
            smali_method += "{}\n".format(line)

    return smali_method

def method_name(main_line, smali_file):
    """
    Returns the first line of the method - method definition - of a method that
    executes the given line

    :param int main_line: the executed line to get the method definition from
    :param str smali_file: the file to extract the method definition from
    :return: a pretty_grep list with the line with the method definition or
    an empty list if not found
    """

    # prepare vraiables and read content
    main_line = int(main_line)
    with open(smali_file, "r") as fp:
        smali = fp.read()

    for i, line in enumerate(reversed(smali.split("\n")[:main_line])):
        if ".method " in line:
            return [{
                "line": main_line - i,
                "details": line.strip()
            }]

    return []

def track_variable(name, line_used, smali_file):
    """
    Tries to identify the last instance a variable was set on the file before
    the line where it was used

    :param str name: the name of the variable (e.g. p1, v2, etc.)
    :param int line_used: the line where the variable is being used
    :param str smali_file: path to the file to look for the variable
    :return: a list with lines where the variable has been set or empty list
    """

    # prepare vraiables and read content
    older_lines =[]
    track_invoke = False
    name = name.lower()
    line_used = int(line_used)
    with open(smali_file, "r") as fp:
        smali = fp.read()

    # go through the lines in reverse looking for initialization
    for i, line in enumerate(reversed(smali.split("\n")[:line_used])):

        if name in line and ("new-" in line or "const" in line):
            return older_lines + [{
                "line": line_used - i,
                "details": line.strip()
            }]


        elif "move-object" in line and name in line:
            older_lines += [{
                "line": line_used - i,
                "details": line.strip()
            }]

            name = line.rsplit(",", 1)[-1].strip()


        elif track_invoke and "invoke" in line:
            return older_lines + [{
                "line": line_used - i,
                "details": line.strip()
            }]

        # if "move-result" then need to check last invoke
        elif "move-result" in line and name in line:
            older_lines += [{
                "line": line_used - i,
                "details": line.strip()
            }]
            track_invoke = True

        # reached method header
        elif ".method " in line:

            # if variable is pX and no other evidence was found then it has
            # been passed over on method call so just return method header
            if name.startswith("p"):
                return older_lines + [{
                    "line": line_used - i,
                    "details": line.strip()
                }]

            # if not variable pX then nothing was found
            else:
                return []

    return []


def string(string_variable, resources_strings_xml_file):
    """
    Looks for a string variable in the resources files

    :param str string_variable: the string variable to look for
    :param str resources_strings_xml_file: the strings.xml file to look for the
    string variable
    :return: the string value of the variable or `string_variable` if not found
    """
    from scrounger.utils.general import pretty_grep

    #replace @string if in variable name
    string_variable = string_variable.replace("@string/", "")

    grep_result = pretty_grep(string_variable, resources_strings_xml_file)

    # if variable was not found
    if len(grep_result) == 0:
        return string_variable

    # get the string from grep result
    string = grep_result.popitem()[1][0]["details"]

    # get the string between tags
    return string.split(">", 1)[-1].split("<", 1)[0]

def parsed_providers(decompiled_app_path):
    """
    Looks for providers and translates any variables returning a uniform list
    of providers

    :param str decompiled_app_path: the directory with the decompiled app
    :return: list with unique provider paths
    """

    # strings xml file
    strings_xml = "{}/res/values/strings.xml".format(decompiled_app_path)

    # extract providers from decompiled app path
    all_providers = extract_providers(decompiled_app_path)

    # get providers from manifest
    manifest = Manifest("{}/AndroidManifest.xml".format(decompiled_app_path))

    # get and parse manifest_providers
    manifest_providers = manifest.providers()
    for provider in manifest_providers:
        provider_string = string(provider["authority"], strings_xml)
        if string(provider["name"]).startswith("."):
            provider_string = "{}{}".format(provider_string,
                string(provider['name'], strings_xml))

        # remove the last forward slash - it will be added in the end
        if provider_string.endswith("/"):
            provider_string = provider_string[:-1]

        all_providers += [provider_string]

    # add providers with a slash in the end
    slash_providers = []
    for provider in all_providers:
        slash_providers += ["{}/".format(provider)]

    return sorted(set(all_providers + slash_providers))

class Manifest(object):
    """ This class represents an Android manifest file """

    BROWSABLE_CATEGORY = "android.intent.category.BROWSABLE"

    def __init__(self, manifest_file_path):
        """
        Create a representation of the Android Manifest object

        :param str manigest_file_path: the path to the manifest file to parse
        """
        import xml.etree.ElementTree as ET

        # get manifest content
        with open(manifest_file_path, "r") as fd:
            manifest_content = fd.read()

        # adjust some content for xml parser to avoid having {android}
        manifest_content = manifest_content.replace(
            "xmlns:android=\"http://schemas.android.com/apk/res/android\" ",
            "").replace("android:", "")

        self._root = ET.fromstring(manifest_content)

    def __str__(self):
        """Returns a string representation of the manifest"""
        return "Android Manifest ({})".format(self.package())

    def version(self):
        """
        Returns the build version name for the app

        :return: the build version number of the app or an empty string if not
        found
        """
        return self._root.get("platformBuildVersionName", "")

    def package(self):
        """
        Returns the package name for the app

        :return: the package name or an empty string if not found
        """
        return self._root.get("package", "")

    def permissions(self):
        """
        Returns a list of permissions being used by the application

        :return: a list of the permissions used
        """
        return [permission.get("name", "") for permission in
            self._root.findall("uses-permission")]

    def providers(self):
        """
        Returns a list of providers specified in the manifest

        :return: a list of dicts of providers containing the name, authorities
        and if they are exported or not
        """
        return [
            { "name": provider.get("name", ""),
              "authorities": provider.get("authorities", ""),
              "exported": provider.get("exported", "false") == "true", }
            for provider in self._root.find("application").findall("provider")]

    def secret_codes(self):
        """
        Returns any secret codes in the manifest

        :return: a list of secret codes
        """
        secret_codes = []

        for receiver in self._root.find("application").findall("receiver"):
            for intent_filter in receiver.findall("intent-filter"):
                for data in intent_filter.findall("data"):
                    code, scheme = data.get("host", ""), data.get("scheme", "")
                    if scheme and code and "android_secret_code" in scheme:
                        secret_codes.append(code)

        return secret_codes

    def _intent_filters(self, activity):
        """
        Returns a list of intenet filters for a given activity

        :param ET.Element activity: the activity to parse
        :return: returns a list of dict of intent-filters with their actions,
        data and categories
        """
        filters = []
        for intent_filter in activity.findall("intent-filter"):
            parsed_filter = {"actions": [], "categories": [], "data": []}

            # get actions
            for action in intent_filter.findall("action"):
                parsed_filter["actions"].append(action.get("name", ""))

            # get categories
            for category in intent_filter.findall("category"):
                parsed_filter["categories"].append(category.get("name", ""))

            # get data
            for data in intent_filter.findall("data"):
                # get key, value attributes
                parsed_filter["data"].append(data.attrib)

            filters.append(parsed_filter)

        return filters

    def activities(self):
        """
        Returns a list of activities and their associated filters, actions, data
        and categories

        :return: a list of dict containing the activities name, their intent
        filters, actions, data and categories
        """
        activities = []
        for activity in self._root.find("application").findall("activity"):
            # add key, value attributes
            parsed_activity = activity.attrib

            # add intents filters
            parsed_activity["intent_filters"] = self._intent_filters(activity)

            activities.append(parsed_activity)

        return activities

    def browsable_activities(self):
        """
        Returns all browsable activities names

        :return: a list of browsable activities names
        """
        activities = []
        for activity in self.activities():
            for intent_filter in activity["intent_filters"]:
                if self.BROWSABLE_CATEGORY in intent_filter["categories"]:
                    activities.append(activity["name"])

        return activities

    def browsable_uris(self):
        """
        Returns a list of browsable uris

        :return: a list of schema://host/path/prefic/pattern
        """
        uris = []
        for activity in self.activities():
            for intent_filter in activity["intent_filters"]:
                if self.BROWSABLE_CATEGORY in intent_filter["categories"]:
                    for data in intent_filter["data"]:

                        # adjust port variable
                        if "port" in data:
                            data["port"] = ":{}".format(data["port"])

                        uris.append("{}://{}{}{}{}{}".format(
                            data.get("scheme", ""), data.get("host", ""),
                            data.get("port", ""), data.get("path", ""),
                            data.get("pathPrefix", ""),
                            data.get("pathPattern", "")))
        return uris

    def main_activity(self):
        """
        Returns the name of the main activity of the application

        :return: package.MainActivityName or None if not found
        """
        MAIN_ACTIVITY_ACTION = "android.intent.action.MAIN"

        package = self.package()

        for activity in self.activities():
            for intent_filter in activity["intent_filters"]:
                if MAIN_ACTIVITY_ACTION in intent_filter["actions"]:
                    return "{}{}".format(package, activity["name"].replace(
                        package, ""))

        return None

    def allow_backup(self):
        """
        Checks if backups are allowed by the application

        :return: True if bakcups are allowed or False otherwise
        """
        return self._root.find("application").get(
            "allowBackup", "false") == "true"

    def debuggable(self):
        """
        Checks if the application is debuggable

        :return: True if the app is debuggable or False otherwise
        """
        return self._root.find("application").get(
            "debuggable", "false") == "true"

    def _get_sdk(self, sdk_type):
        """
        Returns an sdk attribute if defined

        :param str sdk_type: the type of sdk to get: min, max, target
        :return: the sdk attribute or empty string if not defined
        """
        for sdk in self._root.find("application").findall("uses-sdk"):
            if "{}SDKVersion".format(sdk_type.lower()) in sdk.attrib:
                return sdk.get("{}SDKVersion".format(sdk_type.lower()))
        return ""

    def min_sdk(self):
        """
        Returns the minimum SDK supported by the app

        :return: the minimum SDK supported or empty string if not defined
        """
        return self._get_sdk("min")

    def max_sdk(self):
        """
        Returns the maximum SDK supported by the app

        :return: the maximum SDK supported or empty string if not defined
        """
        return self._get_sdk("max")

    def target_sdk(self):
        """
        Returns the target SDK supported by the app

        :return: the target SDK supported or empty string if not defined
        """
        return self._get_sdk("target")

class ApktoolYaml(object):
    """ This object represents an apktool.yml file """

    def __init__(self, yml_file_path):
        """
        Create an object the will represent the Apktool Yaml file

        :param str yml_file_path: the path to the Yaml file
        """
        with open(yml_file_path, 'r') as f:
            self._raw = f.read()

    def __str__(self):
        """Returns a string representation of the apktool yaml"""
        return "Apktool Yaml ({})".format(self.apk_filename())

    def version(self):
        """
        Returns the applications version

        :return: the application version or empty string if not defined
        """
        for line in self._raw.split("\n"):
            if "versionName" in line:
                return line.split(":", 1)[-1].split("'")[1].strip()
        return ""

    def apk_filename(self):
        """
        Returns the applications apk file name

        :return: the application apk file name or empty string if not defined
        """
        for line in self._raw.split("\n"):
            if "apkFileName" in line:
                return line.split(":", 1)[-1].split("'", 1)[-1].replace(
                    "'", "").strip()
        return ""

    def _get_sdk(self, sdk_type):
        """
        Returns an sdk attribute if defined

        :param str sdk_type: the type of sdk to get: min, max, target
        :return: the sdk attribute or empty string if not defined
        """
        for line in self._raw.split("\n"):
            if "{}SdkVersion".format(sdk_type.lower()) in line:
                return line.split(":", 1)[-1].split("'")[1].strip()
        return ""

    def min_sdk(self):
        """
        Returns the minimum SDK supported by the app

        :return: the minimum SDK supported or empty string if not defined
        """
        return self._get_sdk("min")

    def max_sdk(self):
        """
        Returns the maximum SDK supported by the app

        :return: the maximum SDK supported or empty string if not defined
        """
        return self._get_sdk("max")

    def target_sdk(self):
        """
        Returns the target SDK supported by the app

        :return: the target SDK supported or empty string if not defined
        """
        return self._get_sdk("target")
