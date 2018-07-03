#! /usr/bin/env python

from scrounger.utils.config import Log, _BANNER, _SCROUNGER_HOME
from scrounger.utils.general import execute as _execute

from sys import path as _path
import logging as _logging
import argparse as _argparse

# add custom modules path
_modules_path = "{}/modules/".format(_SCROUNGER_HOME)
_path.append(_modules_path)

# define device
_DEVICE = None

# define modifiers
_DEBUG = False
_VERBOSE = False

def _arguments_parser(arguments):
    """Returns a dict with the parsed arguments"""
    arguments = arguments or ""
    result_arguments = {}

    arguments_str_list = arguments.split(";")
    for argument in arguments_str_list:
        if argument:
           key, value = argument.split("=", 1)
           result_arguments[key] = value

    if "output" not in result_arguments or not result_arguments["output"]:
        result_arguments["output"] = "./scrounger-results"

    _execute("mkdir -p {}".format(result_arguments["output"]))

    return result_arguments

def _module_parser(modules):
    """Returns an ordered dict of module classes to be run"""

    if not modules:
        return {}

    modules_str_list = modules.split(";")

    result_modules = {}
    for index, module in enumerate(modules_str_list):
        if module.startswith("custom/"):
            module_class = __import__("{}".format(
                module.replace("/", ".")), fromlist=["Module"])
        else:
            module_class = __import__("scrounger.modules.{}".format(
                module.replace("/", ".")), fromlist=["Module"])
        result_modules[index] = module_class.Module()

    return result_modules

def _device_parser(device, modules_string):
    """Returns a Device object depending on the type of analysis being run"""
    global _DEVICE

    if not device:
        return None

    if "ios" in modules_string:
        from scrounger.utils.ios import devices
        from scrounger.core.device import IOSDevice as Device
    else:
        from scrounger.utils.android import devices
        from scrounger.core.device import AndroidDevice as Device

    dvs = devices()
    if not device and len(dvs) > 0:
        device = dvs.keys()[0]

    _DEVICE = Device(device)
    return _DEVICE

def _run_modules(modules, arguments, device):
    from scrounger.core.module import validate_analysis_result

    modules_instances = _module_parser(modules)
    options = _arguments_parser(arguments)
    if not device and "device" in options:
        device = options["device"]

    device = _device_parser(device, modules)
    options["device"] = device

    for index in modules_instances:
        print("Excuting Module {}".format(index))
        instance = modules_instances[index]

        # set default options first
        for option in instance.options:
            setattr(instance, option["name"], option["default"])

        # set options
        for option in options:
            setattr(instance, option, options[option])

        result = instance.run()

        if "print" in result:
            print("[+] {}".format(result.pop("print")))

        for key in result:
            if key.endswith("_result") and validate_analysis_result(
                result[key]):
                print("[+] Analysis result: {} (Severity: {})".format(
                    result[key]["title"], result[key]["severity"]))
                print("    Should Be Reported: {}".format(
                    "Yes" if result[key]["report"] else "No"))

                if _VERBOSE:
                    print("    Details:\n{}".format(result[key]["details"]))

def _run_full_android(app_path, full_analysis_module, options):
    from scrounger.modules.misc.android import decompile_apk
    from scrounger.modules.misc.android.app import manifest, source

    Log.info("Installing APK")

    # install apk
    if "device" in options and options["device"]:
        options["device"].install(app_path)

    if "apk" not in options:
        options["apk"] = app_path

    Log.info("Decompiling APK")

    # decompile apk
    if "decompiled_apk" not in options:
        decompile_module = decompile_apk.Module()
        decompile_module.apk = app_path
        decompile_module.output = options["output"]
        result = decompile_module.run()
        options["decompiled_apk"] = [
            result[key] for key in result if key.endswith("_decompiled")][0]

    Log.info("Reading Manifest")

    manifest_module = manifest.Module()
    manifest_module.decompiled_apk = options["decompiled_apk"]
    result = manifest_module.run()
    manifest = [result[key] for key in result if key.endswith("_manifest")][0]

    Log.info("Setting Identifier")

    # set identifier
    if "identifier" not in options:
        options["identifier"] = manifest.package()

    Log.info("Getting App's Source")

    # get source
    if "source" not in options:
        source_module = source.Module()
        source_module.apk = app_path
        source_module.output = options["output"]
        result = source_module.run()
        options["source"] = [
            result[key] for key in result if key.endswith("_source")][0]

    Log.info("Setting Options")

    # set options
    for option in options:
        setattr(full_analysis_module, option, options[option])

    Log.info("Running Analysis")

    # run analysis
    return full_analysis_module.run()

def _run_full_ios(app_path, full_analysis_module, options):
    from scrounger.modules.misc.ios import unzip_ipa
    from scrounger.modules.misc.ios.local import class_dump
    from scrounger.modules.misc.ios.local.app import info
    from scrounger.utils.ios import application_path

    Log.info("Installing App")

    # install the application
    if "device" in options and options["device"]:
        options["device"].install(app_path)

    Log.info("Unzipping IPA")

    # unzip the application
    if "unzipped_ipa" not in options:
        unzip_module = unzip_ipa.Module()
        unzip_module.ipa = app_path
        unzip_module.output = options["output"]
        result = unzip_module.run()
        options["unzipped_ipa"] = [
            result[key] for key in result if key.endswith("_unzipped")][0]

    Log.info("Getting Info.plist")

    # get local info plist
    info_module = info.Module()
    info_module.unzipped_ipa = options["unzipped_ipa"]
    info_module.output = options["output"]
    result = info_module.run()
    info = [result[key] for key in result if key.endswith("_info")][0]

    if "info" not in options:
        options["info"] = [
            result[key] for key in result if key.endswith("_info_file")][0]

    unzipped_app_path = application_path(options["unzipped_ipa"])

    # get binary path
    if "binary" not in options:
        options["binary"] = "{}/{}".format(unzipped_app_path,
            info["CFBundleExecutable"])

    # get identifier
    if "identifier" not in options:
        options["identifier"] = info["CFBundleIdentifier"]

    Log.info("Dumping Classes")

    # dump classes
    if "class_dump" not in options:
        class_dump_module = class_dump.Module()
        class_dump_module.binary = options["binary"]
        class_dump_module.output = options["output"]
        result = class_dump_module.run()
        options["class_dump"] = [
            result[key] for key in result if key.endswith("_dump_path")][0]

    Log.info("Setting Options")

    # set options
    for option in options:
        setattr(full_analysis_module, option, options[option])

    Log.info("Running Analysis")

    # run analysis
    return full_analysis_module.run()

def _run_full_analysis(app_path, arguments, device):
    full_analysis_name = "analysis.{}.full_analysis".format(
        "ios" if app_path.lower().endswith(".ipa") else "android"
    )

    Log.info("Preparing arguments")

    options = _arguments_parser(arguments)
    if not device and "device" in options:
        device = options["device"]

    Log.info("Preparing devices")

    device = _device_parser(device, full_analysis_name)
    options["device"] = device

    Log.info("Preparing module")

    module_class = __import__("scrounger.modules.{}".format(full_analysis_name),
        fromlist=["Module"])
    instance = module_class.Module()
    for option in instance.options:
        setattr(instance, option["name"], option["default"])

    if "ios" in full_analysis_name:
        results = _run_full_ios(app_path, instance, options)
    else:
        results = _run_full_android(app_path, instance, options)

    # print results and exceptions
    print(results["print"])
    if "exceptions" in results and results["exceptions"]:
        print("\nThe following exceptions occurred when running the checks:")
        print("\n".join([
            "{}: {}".format(e["module"],e["exception"])
            for e in results["exceptions"]
        ]))

def _print_lists():
    import scrounger.modules

    modules_path = "{}/".format(scrounger.modules.__path__[0])
    modules = _execute("find {} -name '*.py'".format(modules_path))

    available_modules = [
        module.replace(modules_path, "").replace(".py", "")
        for module in modules.split("\n")
        if module and "__" not in module and "full_analysis" not in module
    ]

    # add custom modules
    modules_path = "{}/modules/".format(_SCROUNGER_HOME)
    modules = _execute("find {} -name \"*.py\"".format(modules_path))

    #self._custom_modules = [
    available_modules += [
        module.replace(modules_path, "").replace(".py", "")
        for module in modules.split("\n")
        if module and "__" not in module
    ]

    print("\nAvailable Modules:")
    for module in sorted(available_modules):
        print "    {}".format(module[1:] if module.startswith("/") else module)

    print("\nIOS Devices:")
    from scrounger.utils.ios import devices as ios_devices
    devices = ios_devices()
    for device in devices:
        print "    {}".format(device)

    if not devices:
        print "    None"

    print("\nAndroid Devices:")
    from scrounger.utils.android import devices as android_devices
    devices = android_devices()
    for device in devices:
        print "    {}".format(device)

    if not devices:
        print "    None"

def _print_list(header, list_items, description=None):
    if description:
        print("\n{}:".format(description))

    # calculate max lens
    lens = {}
    for key in header:
        max_len = len(str(header[key])) + 1
        for item in list_items:
            max_len = max(max_len, len(str(item[key])) + 1)
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
    print(header_line + second_line)

    for item in list_items:
        line = "    " if description else ""
        for key in item:
            space_no = lens[key] - len(str(item[key]))
            line += "{}{}".format(item[key], " "*space_no)

        print(line)

def _print_modules_options(modules, full_analysis):
    instances = []
    if full_analysis:
        ios_module_class = __import__("scrounger.modules.analysis.ios.\
full_analysis", fromlist=["Module"])
        android_module_class = __import__("scrounger.modules.analysis.android.\
full_analysis", fromlist=["Module"])
        instances = [ios_module_class.Module(), android_module_class.Module()]

    parsed_modules = _module_parser(modules)
    instances += [parsed_modules[key] for key in parsed_modules]

    header = {1: "Name", 2: "Required", 3: "Description", 4: "Default"}
    for module in instances:
        list_items = [
            {1: option["name"], 2: option["required"],
            3: option["description"], 4: option["default"]}
            for option in module.options
        ]

        _print_list(header, list_items, "Module Options ({})".format(
            module.name()))

def _main():
    global _DEBUG, _VERBOSE

    parser = _argparse.ArgumentParser(description=_BANNER,
        formatter_class=_argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-m", "--modules", required=False,
        metavar="analysis/ios/module1;analysis/ios/module2",
        help="modules to be run - seperated by ; - will be run in order")
    parser.add_argument("-a", "--arguments", required=False,
        metavar="argument1=value1;argument1=value2;",
        help="arguments for the modules to be run")
    parser.add_argument("-f", "--full-analysis", required=False,
        metavar="/path/to/the/app.[apk|ipa]",
        help="runs a full analysis on the application")
    parser.add_argument("-d", "--device", required=False,
        metavar="device_id", default=None,
        help="device to be used by the modules")
    parser.add_argument("-l", "--list", required=False,
        action="store_true", default=False,
        help="list available devices and modules")
    parser.add_argument("-o", "--options", required=False,
        action="store_true", default=False,
        help="prints the required options for the selected modules")
    parser.add_argument("-V", "--verbose", required=False,
        action="store_true", default=False,
        help="prints more information when running the modules")
    parser.add_argument("-D", "--debug", required=False,
        action="store_true", default=False,
        help="prints more information when running scrounger")

    args = parser.parse_args()

    _DEBUG = args.debug
    _VERBOSE = args.verbose

    if _DEBUG:
        Log.setLevel(_logging.DEBUG)

    try:
        if args.list:
            _print_lists()
        elif args.options:
            _print_modules_options(args.modules, args.full_analysis)
        elif args.full_analysis:
            _run_full_analysis(args.full_analysis, args.arguments, args.device)
        elif args.modules:
            _run_modules(args.modules, args.arguments, args.device)
        else:
            parser.print_help()
    except Exception as e:
        print("[-] {}".format(e))

        # print debug
        if _DEBUG:
            import traceback
            print(traceback.format_exc())

    if _DEVICE:
        _DEVICE.clean()

if __name__ == '__main__':
    _main()