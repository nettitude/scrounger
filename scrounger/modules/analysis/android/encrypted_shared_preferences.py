from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from langdetect import detect_langs
from time import sleep

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Looks into the shared preference files and tries to \
check if the contents are encrypted",
        "certainty": 70
    }

    options = [
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        },
        {
            "name": "min_percentage",
            "description": "percentage of certainty required to be language",
            "required": True,
            "default": 90
        },
        {
            "name": "identifier",
            "description": "the application's identifier",
            "required": True,
            "default": None
        },
    ]

    def run(self):
        result = {
            "title": "Application Does Not Encrypt Shared Preferences",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        if not self.device.installed(self.identifier):
            return {"print": "Application not installed"}

        Log.info("Starting the application")
        self.device.start(self.identifier)
        sleep(5)

        Log.info("Finding files in application's data")
        target_paths = ["{}/shared_prefs".format(file_path) for file_path in
            self.device.data_paths(self.identifier)]

        listed_files = []
        report_files = []
        for data_path in target_paths:
            listed_files += self.device.find_files(data_path)

        Log.info("Analysing application's data")

        for filename in listed_files:
            if filename:
                file_content = self.device.file_content(filename)

                lang = detect_langs(file_content)[0]
                Log.debug("{} language {}: {}".format(filename,
                    lang.lang, lang.prob))

                if lang.prob > float("0.{}".format(self.min_percentage)):
                    report_files += [filename]

        if report_files:
            result.update({
                "report": True,
                "details": "* Unencrypted Files:\n * {}".format("\n * ".join(
                    report_files))
            })

        return {
            "{}_result".format(self.name()): result
        }

