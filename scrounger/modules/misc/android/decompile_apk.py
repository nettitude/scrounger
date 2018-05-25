from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import execute
from scrounger.utils.android import decompile
from scrounger.utils.config import Log

from scrounger.modules.misc.android.app.manifest import Module as ManifestModule

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Decompiles an APK file into the output directory",
        "certainty": 100
    }

    options = [
        {
            "name": "output",
            "description": "local output directory",
            "required": True,
            "default": None
        },
        {
            "name": "apk",
            "description": "local path to the APK file",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        Log.info("Creating decompilation directory")

        # create decompiled directory
        identifier = self.apk.rsplit("/", 1)[-1].lower().rsplit(".", 1)[0]
        output_path = "{}/{}.decompiled".format(self.output, identifier)
        execute("mkdir -p {}".format(output_path))

        # unzip
        Log.info("Decompiling application")
        decompile(self.apk, output_path)

        # get identifier
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = output_path
        self.manifest = manifest_module.run()
        if "print" not in self.manifest:
            identifier = self.manifest.popitem()[1].package()

            # move decompiled app to new path
            old_output_path = output_path
            output_path = "{}/{}.decompiled".format(self.output, identifier)
            execute("mv {} {}".format(old_output_path, output_path))

        return {
            "{}_decompiled".format(identifier): output_path,
            "print": "Application decompiled to {}".format(output_path)
        }

