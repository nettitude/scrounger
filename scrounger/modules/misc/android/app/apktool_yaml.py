from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.android import ApktoolYaml
from scrounger.utils.config import Log
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule

from os.path import exists

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Returns the contents of the application's apktool.yml \
in object format",
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
        Log.info("Checking for apktool.yml file")

        # find apktool yml file
        filename = "{}/apktool.yml".format(self.decompiled_apk)

        if exists(filename):
            Log.info("Creating apktool yaml object")

            # get info
            yaml = ApktoolYaml(filename)

            # get identifier
            identifier = yaml.apk_filename().lower().rsplit(".", 1)[0]

            manifest_module = ManifestModule()
            manifest_module.decompiled_apk = self.decompiled_apk
            self.manifest = manifest_module.run()
            if "print" not in self.manifest:
                identifier = self.manifest.popitem()[1].package()

            return {
                "{}_yaml".format(identifier): yaml
            }

        return {"print": "Could not find apktool.yml"}

