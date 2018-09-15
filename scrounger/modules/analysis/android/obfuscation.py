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
            "default": 20
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
            "details": "",
            "severity": "Medium",
            "report": False
        }

        exceptions = []

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
                exceptions += [Exception(self.manifest["print"])]

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

        Log.info("Analysing identified strings")

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
                "details": "Detected language {} with probability {}% on \
class names.".format(class_detect_lang.lang, class_detect_lang.prob*100),
                "report": True
            })

        # check small_classes/total_classes >= min_percent_class_names
        sclass_percent = len(class_small_names)*1.0/len(class_names_list)*100
        if sclass_percent >= self.min_percentage_small_names:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected small class names: {}%".format(
                    result["details"], sclass_percent),
                "report": True
            })

        Log.debug("Classes detected {} with probability of {}%".format(
            class_detect_lang.lang, class_detect_lang.prob*100
        ))
        Log.debug("Small len classes {}/{} = {}%".format(
            len(class_small_names), len(class_names_list), sclass_percent
        ))
        Log.debug("Unique small len classes {}/{} = {}%".format(
            len(set(class_small_names)), len(set(class_names_list)),
            len(set(class_small_names))*1.0/len(set(class_names_list))*100
        ))

        # analyse method names
        method_detect_lang = detect_langs(" ".join(method_names_list))[0]
        method_small_names = [
            method_name for method_name in method_names_list
            if len(method_name) < 4
        ]

        # check if lang != expected or probability lower than required for
        # method names
        if method_detect_lang.lang != self.language or \
        method_detect_lang.prob*100 < self.min_percentage:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected language {} with probability {}% on \
method names.".format(result["details"], method_detect_lang.lang,
                    method_detect_lang.prob*100),
                "report": True
            })

        # check small_methods/total_methods >= min_percent_mathod_names
        smthod_percent = len(method_small_names)*1.0/len(method_names_list)*100
        if smthod_percent >= self.min_percentage_small_names:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected small method names: {}%".format(
                    result["details"], smthod_percent),
                "report": True
            })

        Log.debug("Methods detected {} with probability of {}%".format(
            method_detect_lang.lang, method_detect_lang.prob*100
        ))
        Log.debug("Small len methods {}/{} = {}%".format(
            len(method_small_names), len(method_names_list), smthod_percent
        ))
        Log.debug("Unique small len classes {}/{} = {}%".format(
            len(set(method_small_names)), len(set(method_names_list)),
            len(set(method_small_names))*1.0/len(set(method_names_list))*100
        ))

        # analyse strings and resources
        strings_detect_lang = detect_langs(
            " ".join(strings_list + resources_list))[0]

        # check if lang != expected or probability lower than required for
        # strings and resources
        if strings_detect_lang.lang != self.language or \
        strings_detect_lang.prob*100 < self.min_percentage:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected language {} with probability {}% on \
strings and resources.".format(result["details"], strings_detect_lang.lang,
                    strings_detect_lang.prob*100),
                "report": True
            })

        Log.debug("Strings detected {} with probability of {}%".format(
            strings_detect_lang.lang, strings_detect_lang.prob*100
        ))

        if not result["report"]:
            result.update({
                "details": "No evidence of obfuscation found."
            })

        return {
            "{}_result".format(self.name()): result,
            "exceptions": exceptions
        }

