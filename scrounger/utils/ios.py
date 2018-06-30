"""
Module with ios utility functions.
"""

from scrounger.utils.general import requires_binary
from scrounger.utils.general import execute as _execute

def devices():
    """
    Find connected iDevices

    :return: a list of idevice UDIDs and Names
    """
    @requires_binary("lsusb")
    @requires_binary("grep")
    def _connected_devices():
        from scrounger.utils.general import remove_multiple_spaces

        output = _execute("lsusb -v | grep -E \"idVendor|idProduct|iSerial\"")
        devices = {}

        # finds apple devices
        lines = iter(output.split("\n"))
        for vendor in lines:
            product, serial = next(lines, ""), next(lines, "")
            if "apple" in vendor.lower():
                serial = serial.strip().rsplit(" ", 1)[-1]
                devices[serial] = remove_multiple_spaces(
                    product).split(" ", 2)[-1]
        return devices

    return _connected_devices()

def plist_to_dict(plist):
    """
    Converts a plist file output to a python dictionary

    :param str plist: the output of a plist file
    :return: a dict with the plist contents
    """
    import biplist
    return biplist.readPlistFromString(plist)

def plist_dict_to_xml(plist, key=None):
    """
    Converts a plist dict into an xml string

    :param dict plist: the plist to convert
    :param str key: if the key is set and in the plist it will be the only tag
    returned
    :return: an xml string containing the plist
    """
    import plistlib
    if key and key in plist:
        plist = plist[key]
    xml = plistlib.writePlistToString(plist)
    return '\n'.join(xml.split('\n')[3:-2])

def otool_symbols(local_app_binary):
    """
    Returns the symbols table from a local iOS app using otool

    :param str local_app_binary: the path to the app to get the symbols from
    :return: the symbols table
    """
    @requires_binary("otool")
    def _otool_symbols(local_app_binary):
        # prepare binary
        local_app_binary = local_app_binary.replace(" ", "\ ")
        return _execute("otool -Iv {}".format(local_app_binary))

    return _otool_symbols(local_app_binary)

def jtool_symbols(local_app_binary):
    """
    Returns the symbols table from a local iOS app using jtool

    :param str local_app_binary: the path to the app to get the symbols from
    :return: the symbols table
    """
    @requires_binary("jtool")
    def _jtool_symbols(local_app_binary):
        # prepare binary and assume arm64 arch
        local_app_binary = local_app_binary.replace(" ", "\ ")
        arch = jtool_archs(local_app_binary)[-1]
        return _execute("jtool -S -arch {} {}".format(arch, local_app_binary))

    return _jtool_symbols(local_app_binary)

def otool_flags(local_app_binary):
    """
    Returns the compilation flags from an iOS app using otool

    :param str local_app_binary: the path to the app to get the flags from
    :return: the flags
    """

    @requires_binary("otool")
    def _otool_flags(local_app_binary):
        # prepare binary
        local_app_binary = local_app_binary.replace(" ", "\ ")
        return _execute("otool -hv {}".format(local_app_binary))

    return _otool_flags(local_app_binary)

def jtool_flags(local_app_binary):
    """
    Returns the compilation flags from an iOS app using jtool

    :param str local_app_binary: the path to the app to get the flags from
    :return: the flags
    """
    @requires_binary("jtool")
    def _jtool_flags(local_app_binary):
        # prepare binary and assume arm64 arch
        local_app_binary = local_app_binary.replace(" ", "\ ")
        arch = jtool_archs(local_app_binary)[-1]
        return _execute("jtool -v -h -arch {} {}".format(arch,local_app_binary))

    return _jtool_flags(local_app_binary)

def entitlements(local_app_binary):
    """
    Returns entitlements of a binary app installed on ios

    :param str local_app_binary: the app to check the entitlements from
    :return: a dict with the entitlements
    """
    @requires_binary("ldid")
    def _entitlements(local_app_binary):
        # prepare binary
        local_app_binary = local_app_binary.replace(" ", "\ ")
        ents_str = _execute("ldid -e {}".format(local_app_binary))

        # fix multiple entitlements for multiple archs
        """
        ents = ""
        for line in ents_str.split("\n"):
            if not line: break
            ents += line
        """

        ents = "{}</plist>".format(ents_str.split("</plist>")[0])

        return plist_to_dict(ents)


    return _entitlements(local_app_binary)

def jtool_archs(local_app_binary):
    """
    Get available archs from the binary

    :param str local_app_binary: the app to get the archs from
    :return: a list with the available archs
    """
    import re
    archs = []

    local_app_binary = local_app_binary.replace(" ", "\ ")
    archs_result = _execute("jtool -v -h {}".format(local_app_binary))

    # check for multiple archs
    arch_no = re.findall(r"\d+\ architecture", archs_result)
    if len(arch_no) > 0:
        arch_no = int(arch_no[0].split(" ", 1)[0])
        for arch in re.findall(r"arm(v6|v6s|v7|64)", archs_result):
            archs += ["arm{}".format(arch)]

        # for some reason jtool doesnt display arm64
        if len(archs) < arch_no:
            archs += ["arm64"]

        return archs

    # only 1 arch
    return ["arm{}".format(arch)
        for arch in re.findall(r"arm(v6|v6s|v7|64)", archs_result.lower())]


def otool_archs(local_app_binary):
    """
    Get available archs from the binary

    :param str local_app_binary: the app to get the archs from
    :return: a list with the available archs
    """
    import re

    # get flags
    flags = otool_flags(local_app_binary)

    return map(lambda arch: "arm{}".format(arch),
        re.findall(r"arm[ ]+(v6|v7|v7s|64) ", flags.lower()))

def application_path(root_path):
    """
    Given a root path try to identify the application's path returning the
    /path/to/Payload/App.app

    :param str root_path: path to start looking from
    :return: the path to the application or "" if not found
    """

    if root_path.endswith("/"):
        root_path = root_path[:-1]

    if root_path.endswith(".app"):
        return root_path

    found_apps = _execute("find {} -name \"*.app\"".format(root_path))
    return found_apps.split("\n")[0]

def info(local_application_path):
    """
    Retreived information about the application

    :param str local_application_path: application's path to get the information
    from
    :return: a dict with the information about the application
    """

    return plist("{}/Info.plist".format(local_application_path))

def plist(local_file):
    """
    Reads and returns a plist file in dict form

    :param str local_file: the plist list file to read
    :return: a dict with the plist content
    """
    import biplist
    return biplist.readPlist(local_file)

def unzip(local_ipa_file, target_path):
    """
    Unzips an ipa file to target location

    :param str local_ipa_file: the file path to the IPA
    :param str target_path: the target path to unzip the app too
    :return: nothing
    """
    @requires_binary("unzip")
    def _unzip(local_ipa_file, target_path):
        #clean path before
        _execute("rm -rf {}".format(target_path))
        _execute("unzip -o {} -d {}".format(local_ipa_file, target_path))

    _unzip(local_ipa_file, target_path)

def otool_class_dump(local_app_binary):
    """
    Dumps classes of an ios application using otool

    :param str local_app_binary: the application binary to dump classes from
    :return: a str with the output of otool
    """
    @requires_binary("otool")
    def _otool_class_dump(local_app_binary):
        # prepare binary
        local_app_binary = local_app_binary.replace(" ", "\ ")
        return _execute("otool -ov {}".format(local_app_binary))

    return _otool_class_dump(local_app_binary)

def jtool_class_dump(local_app_binary):
    """
    Dumps classes of an ios application using jtool

    :param str local_app_binary: the application binary to dump classes from
    :return: a str with the output of jtool
    """
    @requires_binary("jtool")
    def _jtool_class_dump(local_app_binary):
        # prepare binary and assume arm64 arch
        local_app_binary = local_app_binary.replace(" ", "\ ")
        return _execute("jtool -v -d objc -arch arm64 {}".format(
            local_app_binary))

    return _jtool_class_dump(local_app_binary)

def save_class_dump(class_dump, local_file_path):
    """
    Saves the class dump into seperate files

    :param dict class_dump: a parsed dict of a class dump of an app
    :param str local_file_path: the file path to save the class dump to
    :return: nothing

    Class format:
    //
    //
    //    Generated by Scrounger v1.0
    //
    //    ClassName
    //

    // base properties

    // instance_properties

    // base_methods

    // instance_ methods

    // protocols
    """
    from scrounger.utils.config import _VERSION
    header = """
//
//
//    Generated by Scrounger v{}
//
//    {}
//

"""

    attribute = """
// {}
{}

"""
    for app_class in class_dump:
        file_name = "{}/{}.h".format(local_file_path, app_class["name"])
        with open(file_name, "w") as fp:
            fp.write(header.format(_VERSION, app_class["name"]))

            for field_type in app_class:
                if field_type != "name":
                    fp.write(attribute.format(field_type.replace("_", " "),
                        "\n".join(app_class[field_type])))

def jtool_class_dump_to_dict(output):
    """
    Parses the output of a class dump from jtool to a dictionary

    :param str ouput: the class dump output to parse
    :return: a dict with the parsed classes, methods, properties and
    functions
    """
    parsing_types = {
        "properties": "base_properties",
        "instance variable": "instance_properties",
        "instance methods": "instance_methods",
        "class methods": "base_methods",
    }

    classes = []
    working_class = None
    parsing_type = ""
    collected_types = []

    for line in output.split("\n"):

        if any(key in line for key in parsing_types):
            if working_class and collected_types and parsing_type:
                working_class[parsing_type] = collected_types
                collected_types = []
                parsing_type = ""

            for key in parsing_types:
                if key in line:
                    parsing_type = parsing_types[key]

        elif "Dumping class" in line:
            working_class = {
                "name": line.split("(", 1)[-1].strip()[:-1]
            }

        elif line.startswith("//"):
            continue

        elif "@end" in line:
            working_class[parsing_type] = collected_types
            classes += [working_class]
            working_class = None
            parsing_type = ""
            collected_types = []

        elif working_class and parsing_type == "base_properties":
            collected_types += [line.split("//", 1)[0].strip()]

        elif working_class and parsing_type == "instance_properties":
            attribute_type = _get_attribute_type(line.split("//", 1)[-1])
            parsing_name = line.rsplit(";", 1)[0].rsplit(" ", 1)[-1].strip()

            collected_types += ["{} {};".format(attribute_type, parsing_name)]

        elif working_class and (parsing_type == "instance_methods" or \
            parsing_type == "base_methods"):
            method_types = _get_types(line.strip().split("// Protocol ", 1)[-1])
            method_name = line.split("/ ", 1)[-1][2:].split(";", 1)[0].strip()
            full_method_name = _get_method_name(method_name, method_types[1:])

            collected_types += ["{} ({}){};".format(
                "-" if parsing_type == "instance_methods" else "+",
                method_types[0], full_method_name)]

    return classes

def otool_class_dump_to_dict(output):
    """
    Parses the output of a class dump from otool to a dictionary

    :param str ouput: the class dump output to parse
    :return: a dict with the parsed classes, methods, properties and
    functions
    """
    parsing_types = {
        "baseProperties": "base_properties",
        "instanceProperties": "instance_properties",
        "instanceMethods": "instance_methods",
        "baseProtocols": "protocols",
        "baseMethods": "base_methods"
    }

    # prepare variables
    classes = []
    working_class = None
    parsing_type = parsing_name = ""

    # parse output
    for line in output.split("\n"):
        parsing_types_found = [ptype in line for ptype in parsing_types]

        # start parsing class
        if working_class == None and "struct class_ro_t" in line:
            parsing_type = "class"

            #if working_class != None and "name" in working_class:
                #classes += [working_class]

            working_class = {}

        elif parsing_type == "class" and "name" in line:
            working_class["name"] = _get_name(line)

        # starting different class
        elif working_class != None and not line.startswith("    ")\
        and not line.startswith("\t") and not line.startswith("Meta Class"):
            # check if last class was fully parsed and save it
            if "name" in working_class:
                classes += [working_class]

            # clean helper variables
            working_class = None
            parsing_name = parsing_type = ""

        # parse methods and properties names
        elif working_class != None and any(parsing_types_found):
            parsing_type = parsing_types.values()[
                parsing_types_found.index(True)]

            if parsing_type not in working_class:
                working_class[parsing_type] = []

        elif parsing_type in parsing_types.values() and "name" in line:
            parsing_name = _get_name(line)

        # parse properties
        elif parsing_type == "base_properties" and parsing_name\
        and "attributes" in line:
            attribute_type = _get_attribute_type(line)
            attribute_properties = _get_attribute_properties(line)

            working_class["base_properties"] += ["@property{} {} {};".format(
                attribute_properties, attribute_type, parsing_name)]

            parsing_name = ""

        elif parsing_type == "instance_properties" and parsing_name\
        and "type" in line:
            attribute_type = _get_attribute_type(line)

            working_class["instance_properties"] += ["{} {};".format(
                attribute_type, parsing_name)]

            parsing_name = ""

        # parse methods
        elif parsing_type == "instance_methods" and parsing_name\
        and "types" in line:
            method_types = _get_types(line.strip().split(" ", 2)[-1])
            full_method_name = _get_method_name(parsing_name, method_types[1:])

            working_class["instance_methods"] += ["+ ({}){};".format(
                method_types[0], full_method_name)]

            parsing_name = ""

        elif parsing_type == "base_methods" and parsing_name\
        and "types" in line:
            method_types = _get_types(line.strip().split(" ", 2)[-1])
            full_method_name = _get_method_name(parsing_name, method_types[1:])

            working_class["base_methods"] += ["- ({}){};".format(
                method_types[0], full_method_name)]

            parsing_name = ""

        # parse protocols
        elif parsing_type == "protocols" and parsing_name and "type" in line:
            protocol_type = _get_attribute_type(line)

            working_class["protocols"] += ["{} {};".format(protocol_type,
                parsing_name)]

            parsing_name = ""

        # reached the end of the classes
        elif 'Contents of' in line\
        and not "Contents of (__DATA,__objc_classlist) section" in line:
            break

        parsing_types_found = []

    return classes

def _get_name(name_string):
    """
    Parses the name of a method, class, attribute, property from a class dump

    :param str name_string: the string from a class dump to be parsed
    :return: the name found on the string
    """
    return name_string.strip().rsplit(" ", 1)[-1].strip()

def _get_types(type_string):
    """
    Parses a string a a list of types on the string

    :param str type_string: the string from a class dump to be parsed
    :return: a list with types
    """
    known_types = {
        "v": "void",
        "f": "float",
        "s": "short", "S": "short",
        "I": "unsigned int",
        "C": "unsigned char",
        "i": "long long", "q": "long long",
        "d": "double",
        "B": "Bool", "c": "Bool", "Q": "Bool",
        "l": "long", "L": "long",
        "*": "char * ",
        "@": "id",
        "#": "Class",
        ":": "SEL",
        "%": "UnkownType"
    }

    # replace unkown types
    type_string = type_string.replace(
        "@0:", "").replace("@?", "%").replace("^?", "%")

    # prepare variables
    types = []
    new_type = None
    new_type_found = 0 # there can be nested new types - just parsing the first

    # parse string
    for char in type_string:

        # found new type
        if char == "{":
            new_type_found += 1
            if new_type_found == 1:
                new_type = ""

        # save new type
        elif char == "=" and new_type_found:
            types += ["struct {}".format(new_type)]
            new_type = None

        # parsing new type name
        elif new_type_found > 0 and new_type != None:
            new_type += char

        # stop parsing new type
        elif char == "}":
            new_type_found -= 1

        # check if known type
        elif char in known_types and new_type_found == 0:
            types += [known_types[char]]

    return types

def _get_method_name(name_string, types):
    """
    Returns the method name with the correct parsed types for the arguments

    :param str name_string: a string from a class dump that contains the name of
    the method without the types
    :param list types: a list of types for the arguments of the method
    :return: a str with the method name and types of arguments
    """

    # return the name of the method without arguments
    if len(types) == 0:
        return name_string.replace(":", "")

    # add void types if there are more arguments than types
    while name_string.count(":") > len(types):
        types += ["void"]

    typed_method_name = []
    # [:-1] since the last : would generate an empty argument
    for index, partial_method_name in enumerate(name_string.split(":")[:-1]):
        # format is [partial method name]:([type])[argument name]
        typed_method_name += ["{}:({})arg{}".format(partial_method_name,
            types[index], (index+1))]

    return " ".join(typed_method_name)

def _get_attribute_type(attribute_string):
    """
    Returns the type of an attribute given in a string

    :param str attribute_string: the string from a class dump containing an
    attribute
    :return: a string with the attribute type
    """
    import re

    # split the whole string by spaces to get the last argument which contains
    # the type and the properties of the attribute - [0] gets only the type
    attribute_string = attribute_string.rsplit(" ", 1)[-1].split(",")[0]
    #line.strip().rsplit(' ', 1)[-1]


    # unkown symbol - may indicate struct
    if attribute_string.startswith("T"):
        attribute_string = attribute_string[1:]

    # check if pointer
    if attribute_string.startswith("@\""):
        # get content between "
        return "{} *".format(attribute_string.split("\"")[-2])

    attribute_type = _get_types(attribute_string)

    # if attribute type not found default to id
    if not attribute_type:
        return "id"

    return attribute_type[0]

def _get_attribute_properties(attribute_string):
    """
    Returns the properties of the attribute from a dumped sting

    :param str attribute_string: the string from a class dump containing an
    attribute
    :return: a string containing the parsed properties of an attribute
    """
    known_attributes = {
        "N": "nonatomic",
        "R": "readonly",
        "C": "copy",
        "&": "retain"
    }

    # split the whole string by spaces to get the last argument which contains
    # the type and the properties of the attribute - [1:] gets only the
    # properties
    attributes = attribute_string.rsplit(" ", 1)[-1].split(",")[1:]

    fully_named_attributes = ", ".join([
        known_attributes[attribute] for attribute in attributes
            if attribute in known_attributes])

    # check if weak attribute
    if "W" in attributes:
        return "({}) __weak".format(fully_named_attributes)

    return "({})".format(fully_named_attributes)

