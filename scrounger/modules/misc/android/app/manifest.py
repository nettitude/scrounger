from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.android import Manifest
from scrounger.utils.config import Log
from os.path import exists

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Returns the contents of the application's \
 AndroidManifest.xml in object format",
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
        Log.info("Checking for AndroidManifest.xml file")

        # find manifest file
        filename = "{}/AndroidManifest.xml".format(self.decompiled_apk)

        if exists(filename):
            Log.info("Creating manifest object")

            # get info
            manifest = Manifest(filename)

            return {
                "{}_manifest".format(manifest.package()): manifest
            }

        return {"print": "Could not find AndroidManifest.xml"}

