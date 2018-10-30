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

    regex = r"jailb[a-zA-Z0-9_-]*"

    artefacts = [
        "/system/bin/su",
        "/system/xbin/su",
        "/sbin/su",
        "/system/su",
        "/system/bin/.ext/.su",
        "/system/usr/we-need-root/su-backup",
        "/system/xbin/mu",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/system/sd/xbin/su",
        "/system/bin/failsafe/su",
        "/data/local/su",
        "rootdetect",
        "rootcheck",
        "rooted",
        "substrate",
        "busybox",
        "xposed",
        "supersu",
        "jailb"
    ]

    def run(self):
        result = {
            "title": "Application Does Not Implement Root Detection",
            "details": "",
            "severity": "High",
            "report": True
        }

        # update regex with artefacts, base64 and hex
        for artefact in self.artefacts:
            self.regex = "{}|{}|{}|{}".format(self.regex, artefact,
                artefact.encode("base64"), artefact.encode("hex")
            ).replace("\n", "").replace("=", "").replace("+", "\\+")
            # need to escape + because of the regex grep

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
