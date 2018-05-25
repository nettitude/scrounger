from scrounger.core.module import BaseModule

# helper modules
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's available architectures",
        "certainty": 100
    }

    options = [
        {
            "name": "identifier",
            "description": "the application's identifier",
            "required": True,
            "default": None
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        result = {"print": "Application not installed."}

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            # setup filenames
            remote_binary = "{}/{}".format(
                installed_apps[self.identifier]["application"],
                installed_apps[self.identifier]["display_name"])

            Log.info("Getting architectures")
            flags = self.device.otool("-hv", remote_binary)[0] # stdout
            archs = map(lambda arch: "arm{}".format(arch),
                re.findall(r"arm[ ]+(v6|v7|v7s|64) ", flags.lower()))

            result = {
                "{}_archs".format(self.identifier): archs
            }

        return result

