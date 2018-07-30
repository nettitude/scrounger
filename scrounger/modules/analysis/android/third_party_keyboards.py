from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep
from scrounger.utils.android import smali_dirs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements third-party \
keyboard detection",
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

    regex = r"getInputMethodList"

    def run(self):
        result = {
            "title": "Application Does Not Check For Third-Party Keyboards",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # preparing variable to run
        third_party_keyboard_evidence = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            third_party_keyboard_evidence.update(pretty_grep(self.regex, smali))

            # remove ignored paths
            to_remove = []
            for filename in third_party_keyboard_evidence:
                if any(filepath in filename for filepath in ignore):
                    to_remove += [filename]
            for filename in to_remove:
                third_party_keyboard_evidence.pop(filename)

        if not third_party_keyboard_evidence:
            result.update({"report": True})

        return {
            "{}_result".format(self.name()): result
        }
