from scrounger.core.module import BaseModule

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
        Log.info("Starting application")

        if self.device.installed(self.identifier):

            self.device.start(self.identifier)

            return {
                "print": "Application {} started".format(self.identifier)
            }

        return {
            "print": "Application not installed"
        }

