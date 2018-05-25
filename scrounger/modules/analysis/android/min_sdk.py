from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.apktool_yaml import Module as YamlModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application supports outdated sdks",
        "certainty": 100
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        },
        {
            "name": "minsdk",
            "description": "minimum sdk allowed",
            "required": True,
            "default": 19
        }
    ]

    def run(self):
        result = {
            "title": "The Application Supports Outdated SDKs",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # create yaml
        apktool_module = YamlModule()
        apktool_module.decompiled_apk = self.decompiled_apk
        self.apktool = apktool_module.run()
        if "print" in self.apktool:
            return {"print": "Could not get the apktool yaml file"}

        self.apktool = self.apktool.popitem()[1]

        Log.info("Analysing application's apktool yaml")

        min_sdk = self.apktool.min_sdk()
        if min_sdk and int(min_sdk) < int(self.minsdk):
            result.update({
                "report": True,
                "details": "* Minimum supported SDK \
version\nminSdkVersion=\"{}\"".format(min_sdk)
            })

            if int(min_sdk) < 18:
                result.update({"severity": "High"})

        return {
            "{}_result".format(self.name()): result,
            "{}_minsdk".format(self.apktool.apk_filename()): min_sdk
        }

