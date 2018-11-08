from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Installs an application on the remote device",
        "certainty": 100
    }

    options = [
        {
            "name": "application",
            "description": "local path to the application to be installed",
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
        Log.info("Installing application")
        return {
            "print": "Installation result: {}".format(
                self.device.install(self.application))
        }

