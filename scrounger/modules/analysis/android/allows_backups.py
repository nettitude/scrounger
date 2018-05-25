from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application has `allowbackup` enabled",
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

    """ # LEFT FOR FUTURE REFERENCE
    def validate_options(self):
        super(Module, self).validate_options()

        if self.manifest.__class__.__name__ != "Manifest":
            raise Exception("Variable `manifest` not of type Manifest")
    """

    def run(self):
        result = {
            "title": "The Application Allows Backups",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # create manifest
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        manifest = manifest_module.run()
        if "print" in manifest:
            return {"print": "Could not get the manifest"}

        manifest = manifest.popitem()[1]

        Log.info("Analysing application's manifest")

        if manifest.allow_backup():
            result.update({"report": True})

        return {
            "{}_result".format(self.name()): result
        }

