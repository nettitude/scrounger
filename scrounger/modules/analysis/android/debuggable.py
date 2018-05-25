from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application is set as debuggable",
        "certainty": 100
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        result = {
            "title": "The Application Is Debuggable",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # create manifest
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        self.manifest = manifest_module.run()
        if "print" in self.manifest:
            return {"print": "Could not get the manifest"}

        self.manifest = self.manifest.popitem()[1]

        Log.info("Analysing application's manifest")

        if self.manifest.debuggable():
            result.update({"report": True})

        return {
            "{}_result".format(self.name()): result
        }

