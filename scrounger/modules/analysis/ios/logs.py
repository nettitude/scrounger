from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.info import Module as InfoModule

from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application logs to syslog",
        "certainty": 60
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
        result = {
            "title": "Application Logs To Syslog",
            "details": "",
            "severity": "Low",
            "report": True
        }

        Log.info("Getting executable's name")

        info_module = InfoModule()
        info_module.identifier = self.identifier
        info_module.device = self.device
        info_result, info = info_module.run(), None
        for key in info_result:
            if key.endswith("_info"):
                info = info_result[key]

        if not info:
            return {"print": "Couldn't get Info from device."}

        executable_name = info["CFBundleExecutable"]

        Log.info("Getting application's logs")
        logs = self.device.logs(executable_name)

        if logs:
            result.update({
                "report": True,
                "details": "The following logs were found:\n{}".format(logs)
            })

        return {
            "{}_result".format(self.name()): result
        }

