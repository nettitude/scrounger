from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.android import recompile
from scrounger.utils.config import Log

from scrounger.modules.misc.android.app.manifest import Module as ManifestModule

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Recompiles a decompiled application",
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
            "name": "output",
            "description": "local output directory",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        Log.info("Preparing to re-compile the application")

        # get identifier
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        self.manifest = manifest_module.run()
        if "print" not in self.manifest:
            identifier = self.manifest.popitem()[1].package()

        recompiled_apk = "{}/{}-recompiled.apk".format(self.output, identifier)

        # unzip
        Log.info("Re-compiling application")
        output = recompile(self.decompiled_apk, recompiled_apk)

        if "Exception" in output:
            return {
                "print": "Failed to re-compile the application:\n{}".format(
                    output)
            }

        return {
            "{}_recompiled".format(identifier): recompiled_apk,
            "print": "Application re-compiled to {}".format(recompiled_apk)
        }

