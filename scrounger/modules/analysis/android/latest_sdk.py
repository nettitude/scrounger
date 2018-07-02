from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.apktool_yaml import Module as YamlModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application targets the latest sdk",
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
            "name": "targetsdk",
            "description": "latests sdk",
            "required": True,
            "default": 27
        }
    ]

    def run(self):
        result = {
            "title": "Application Does Not Target The Latest SDK",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # create yaml
        apktool_module = YamlModule()
        apktool_module.decompiled_apk = self.decompiled_apk
        apktool_module.identifier = self.identifier
        self.apktool = apktool_module.run()
        if "print" in self.apktool:
            return {"print": "Could not get the apktool yaml file"}

        self.apktool = self.apktool.popitem()[1]

        Log.info("Analysing application's apktool yaml")

        target_sdk = self.apktool.target_sdk()
        if target_sdk and int(target_sdk) < int(self.targetsdk):
            result.update({
                "report": True,
                "details": "* Current target supported SDK \
version\ntargetSdkVersion=\"{}\"".format(target_sdk)
            })

        return {
            "{}_result".format(self.name()): result,
            "{}_targetsdk".format(self.apktool.apk_filename()): target_sdk
        }

