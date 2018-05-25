from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep
from scrounger.utils.android import smali_dirs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application has screenshot protection \
flags",
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

    regex = r"FLAG_SECURE"
    activities_regex = r"\.method.*onCreate\("

    def run(self):
        result = {
            "title": "Application Does Not Prevent Screenshots",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # preparing variable to run
        report_activities = []
        activities = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali code")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            activities.update(pretty_grep(self.activities_regex, smali))

        if activities:
            safe_activities = pretty_grep(
                self.regex, " ".join(list(activities)))
            report_activities = list(set(activities) - set(safe_activities))

        if report_activities:
            result.update({
                "report": True,
                "details": "\* ".join([activity.replace(self.decompiled_apk, "")
                    for activity in report_activities if not any(
                        i in activity for i in ignore)
                ])
            })

        return {
            "{}_result".format(self.name()): result
        }
