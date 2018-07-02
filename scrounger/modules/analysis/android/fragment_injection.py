from scrounger.core.module import BaseModule

# helper function
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import smali_dirs
from scrounger.modules.misc.android.app.apktool_yaml import Module as YamlModule
from scrounger.utils.config import Log

# TODO: also look at smali code

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application is vulnerable to fragment \
injection attacks",
        "certainty": 50
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

    regex = r"\.super.*PreferenceActivity"

    def run(self):
        result = {
            "title": "Application Is Vulnerable To Fragment Injection",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        # create yaml
        apktool_module = YamlModule()
        apktool_module.decompiled_apk = self.decompiled_apk
        apktool = apktool_module.run()
        if "print" in apktool:
            return {"print": "Could not get the apktool yaml file"}
        apktool = apktool.popitem()[1]

        # preparing variable to run
        activities = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's apktool yaml and smali")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            activities.update(pretty_grep(self.regex, smali))

        if activities and int(apktool.min_sdk()) < 18:
            result.update({
                "report": True,
                "details": pretty_grep_to_str(activities,
                    self.decompiled_apk, ignore)
            })

        return {
            "{}_result".format(self.name()): result
        }

