from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.android import class_names, method_names, app_strings
from scrounger.utils.android import app_used_resources

from langdetect import detect_langs
from time import sleep

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Looks into the application's smali code and tries to \
check if the contents are obfuscated",
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
            "name": "min_percentage",
            "description": "percentage of certainty required to be language",
            "required": True,
            "default": 98
        },
        {
            "name": "language",
            "description": "the language to be detected",
            "required": True,
            "default": "en"
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        }
    ]

    def run(self):
        result = {
            "title": "Application Does Not Use Obfuscation",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        # preparing variable to run
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying class names")
        class_names_list = class_names(self.decompiled_apk, ignore)

        Log.info("Identifying method names")
        method_names_list = method_names(self.decompiled_apk, ignore)

        Log.info("Identifying strings")
        strings_list = app_strings(self.decompiled_apk, ignore)

        Log.info("Identifying resources")
        resources_list = app_used_resources(self.decompiled_apk, ignore)

        class_detect_lang = detect_langs(" ".join(class_names_list))[0]
        class_small_names = [
            class_name for class_name in class_names_list
            if len(class_name) < 4
        ]

        # check if lang != expected or probability lower than required for class
        # names
        if class_detect_lang.lang != self.language or \
        class_detect_lang.prob*100 < self.min_percentage:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected language {} with probability {} on \
class names.".format(result["details"],
                    class_detect_lang.lang, class_detect_lang.prob)
            })

        #b=scrounger.modules.analysis.android.obfuscation.Module();
        #b.decompiled_apk = "/tmp/tests/t2/a";
        #b.ignore="/com/google/;/android/support/"; b.language="en";
        #b.min_percentage=100

        # get function names
        # get var names
        # get strings

        # class name example
        # .class public Lcom/myhost/android/BookingActivity;
        # \.class.*L.*; [split "/" -1 replace ;]

        # function name example
        #.method static synthetic a(Lcom/myhost/android/BookingActivity;)V
        #\.method.*\(.*\) [split "(" 0 rsplit " " -1]

        # strings
        #./android/OpeningActivity.smali:195:    const-string p3, "data"
        #\".*?\"
        #const v1, 0x7f0c0016
        #const.*0x[a-z0-9]{8}

        # count number or method and functions names that are smaller than 4 chars
        # if > 0.4

        """
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
        """

        return {
            "{}_result".format(self.name()): result
        }

