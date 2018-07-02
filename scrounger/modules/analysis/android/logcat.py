from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import smali_dirs, track_variable
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application is logging any details to \
logcat",
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

    regex = r"Log;->(w|i|v|e)"

    def run(self):
        result = {
            "title": "Application Logs To Logcat",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # preparing variable to run
        logs = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            logs.update(pretty_grep(self.regex, smali))


        report = {}
        # check var setting
        for file_name in logs:

            report[file_name] = []

            for instance in logs[file_name]:
                var_name = instance["details"].split(
                    "}", 1)[0].split(",", 1)[-1].strip()

                var_setting = track_variable(
                    var_name, instance["line"], file_name)

                report[file_name] += var_setting

        for file_name in report:
            logs[file_name] += report[file_name]

        if logs:
            result.update({
                "report": True,
                "details": pretty_grep_to_str(logs, self.decompiled_apk, ignore)
            })

        return {
            "{}_result".format(self.name()): result
        }
