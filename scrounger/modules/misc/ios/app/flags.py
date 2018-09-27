from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's compilation flags",
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
                installed_apps[self.identifier]["binary_name"])

            Log.info("Getting binary flags")
            flags = self.device.otool("-hv", remote_binary)[0] # stdout

            result = {
                "{}_flags".format(self.identifier): flags
            }

        return result

