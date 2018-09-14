from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.android import class_names, method_names, app_strings
from scrounger.utils.android import app_used_resources

from scrounger.modules.misc.android.app.manifest import Module as ManifestModule

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
            "name": "min_percentage_small_names",
            "description": "percentage of < 4 chars names to consider the name \
obfuscated",
            "required": True,
            "default": 35
        },
        {
            "name": "language",
            "description": "the language to be detected",
            "required": True,
            "default": "en"
        },
        {
            "name": "check_package_only",
            "description": "looks at the package name and analyses only \
classes that are in the path",
            "required": False,
            "default": "True"
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
            "details": "No evidence of obfuscation found.",
            "severity": "Medium",
            "report": False
        }

        # preparing variable to run
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        # get identifier
        Log.info("Checking identifier package only")
        if self.check_package_only.lower() == "true":
            manifest_module = ManifestModule()
            manifest_module.decompiled_apk = self.decompiled_apk
            self.manifest = manifest_module.run()
            if "print" not in self.manifest:
                identifier = self.manifest.popitem()[1].package()
            else:
                identifier = None
                result.upate({
                    "exceptions": [Exception(self.manifest["print"])]
                })

        Log.info("Identifying class names")
        class_names_list = class_names(self.decompiled_apk, ignore, identifier)

        Log.info("Identifying method names")
        method_names_list = method_names(self.decompiled_apk, ignore,
            identifier)

        Log.info("Identifying strings")
        strings_list = app_strings(self.decompiled_apk, ignore, identifier)

        Log.info("Identifying resources")
        resources_list = app_used_resources(self.decompiled_apk, ignore,
            identifier)

        # start by analysing class names

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
                "details": "Detected language {} with probability {} on \
class names.".format(class_detect_lang.lang, class_detect_lang.prob)
            })

        # check small_classes/total_classes >= min_percent_class_names
        sclass_percent = len(class_small_names)*1.0/len(class_names_list)*100
        if sclass_percent >= self.min_percentage_small_names:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected small class names: {}%".format(
                    sclass_percent)
            })

        # analyse method names



        # analyse strings and resources

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

