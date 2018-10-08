from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

from scrounger.modules.misc.ios.class_dump import Module as ClDumpModule

from langdetect import detect_langs
from time import sleep

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Looks into the application's symbols and strings \
trying to check if the application is obfuscated",
        "certainty": 50
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
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

        # get class dump
        class_dump_module = ClDumpModule()
        class_dump_module.binary = self.binary
        class_dump_module.output = None
        class_dump_result, classes_dumped = class_dump_module.run(), None
        for key in class_dump_result:
            if key.endswith("_class_dump"):
                classes_dumped = class_dump_result[key]

            if key.endswith("exceptions"):
                exceptions += class_dump_result[key]

        Log.info("Analysing class dump")

        class_strings =[]
        for class_dumped in classes_dumped:

            # add to class name list
            class_strings += [class_dumped["name"]]

            # enumerate property names
            if "base_properties" in class_dumped:
                for property_dumped in class_dumped["base_properties"]:
                    class_strings += [
                        property_dumped.rsplit(" ", 1)[-1][:-1]]
            if "instance_property" in class_dumped:
                for property_dumped in class_dumped["instance_property"]:
                    class_strings += [
                        property_dumped.rsplit(" ", 1)[-1][:-1]]

            # enumerate method names
            if "base_methods" in class_dumped:
                for method_dumped in class_dumped["base_methods"]:
                    class_strings += [
                        part.split(":", 1)[0].split(")",1)[-1].replace(";", "")
                        for part in method_dumped.split(" ")
                        if ":" in part
                    ]
            if "instance_methods" in class_dumped:
                for method_dumped in class_dumped["instance_methods"]:
                    class_strings += [
                        part.split(":", 1)[0].split(")",1)[-1].replace(";", "")
                        for part in method_dumped.split(" ")
                        if ":" in part
                    ]

        # put them all together and get an analysis
        class_detect_lang = detect_langs(" ".join(class_strings))[0]
        class_small_strings = [
            string for string in class_strings
            if len(string) < 4
        ]

        # check if lang != expected or probability lower than required for str
        if class_detect_lang.lang != self.language or \
        class_detect_lang.prob*100 < self.min_percentage:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "Detected language {} with probability {}%.".format(
                    class_detect_lang.lang, class_detect_lang.prob*100),
                "report": True
            })

        # check small_strings/total_strings >= min_percentage_small_strings
        sclass_percent = len(class_small_strings)*1.0/len(class_strings)*100
        if sclass_percent >= self.min_percentage_small_names:
            result.update({
                "title": "Application shows evidence of obfuscation",
                "details": "{}\n\nDetected small strings: {}%".format(
                    result["details"], sclass_percent),
                "report": True
            })

        Log.debug("Strings detected {} with probability of {}%".format(
            class_detect_lang.lang, class_detect_lang.prob*100
        ))
        Log.debug("Small len strings {}/{} = {}%".format(
            len(class_small_strings), len(class_strings), sclass_percent
        ))
        Log.debug("Unique small len classes {}/{} = {}%".format(
            len(set(class_small_strings)), len(set(class_strings)),
            len(set(class_small_strings))*1.0/len(set(class_strings))*100
        ))

        if not result["report"]:
            result.update({
                "details": "No evidence of obfuscation found.",
                "report": True
            })

        return {
            "{}_result".format(self.name()): result,
            "exceptions": exceptions
        }

