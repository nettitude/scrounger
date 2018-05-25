from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep, pretty_grep_to_str
from scrounger.utils.android import smali_dirs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application has root detection",
        "certainty": 60
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

    regex = r"rootdetect|rootcheck|jailb[a-zA-Z0-9_-]*|rooted|substrate|\
busybox|c3Vic3RyYXRl|YnVzeWJveA==|eHBvc2Vk|c3VwZXJzdQ=="

    def run(self):
        result = {
            "title": "Application Does Not Have Root Detection",
            "details": "",
            "severity": "High",
            "report": True
        }

        # preparing variable to run
        root_detection = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            root_detection.update(pretty_grep(self.regex, smali))

        if root_detection:
            result = {
                "title": "Application Has Root Detection",
                "details": pretty_grep_to_str(root_detection,
                    self.decompiled_apk, ignore),
                "severity": "Low",
                "report": True
            }

        return {
            "{}_result".format(self.name()): result
        }
