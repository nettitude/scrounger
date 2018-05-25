from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Reports the browsable activities and URIs",
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
            "title": "Application Has Browsable Activities",
            "details": "",
            "severity": "Informational",
            "report": False
        }

        # create manifest
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        self.manifest = manifest_module.run()
        if "print" in self.manifest:
            return {"print": "Could not get the manifest"}

        self.manifest = self.manifest.popitem()[1]

        Log.info("Getting browsable activities and uris")

        browsable_classes = self.manifest.browsable_activities()
        browsable_uris = self.manifest.browsable_uris()

        if browsable_classes or browsable_uris:
            details = "* URIs:\n * {}".format("\n * ".join(browsable_uris))
            details += "\n\n* Classes:\n * {}".format(
                "\n * ".join(browsable_classes))

            result.update({
                "report": True,
                "details": details
            })

        return {
            "{}_result".format(self.name()): result,
            "{}_browsable_classes".format(
                self.manifest.package()): browsable_classes,
            "{}_browsable_uris".format(
                self.manifest.package()): browsable_uris
        }

