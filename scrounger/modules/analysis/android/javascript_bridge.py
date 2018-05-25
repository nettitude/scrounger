from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_multiline_grep
from scrounger.utils.general import pretty_grep_to_str
from scrounger.utils.android import smali_dirs, method_name
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements javascript bridge",
        "certainty": 100
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        }
    ]

    js_interface_regex = r"JavascriptInterface"

    def run(self):
        result = {
            "title": "Application's WebViews Implement Javascript Bridges",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        # preparing variable to run
        bridges = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            bridges = pretty_grep(self.js_interface_regex, smali)

        report = {}
        # check var setting
        for file_name in bridges:
            report[file_name] = []

            for instance in bridges[file_name]:
                report[file_name] += method_name(
                    instance["line"], file_name)

        for file_name in report:
            bridges[file_name] += report[file_name]

        if bridges:
            result.update({
                "report": True,
                "details": pretty_grep_to_str(bridges,
                    self.decompiled_apk, ignore)
            })

        return {
            "{}_result".format(self.name()): result
        }

