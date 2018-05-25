from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Launches an application on the remote device",
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

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            # setup filenames
            remote_binary = "{}/{}".format(
                installed_apps[self.identifier]["application"],
                installed_apps[self.identifier]["display_name"])

            Log.info("Starting the application")
            self.device.start(remote_binary)

            return {
                "print": "Application {} started.".format(self.identifier)
            }

        return {
            "print": "Application not installed."
        }

