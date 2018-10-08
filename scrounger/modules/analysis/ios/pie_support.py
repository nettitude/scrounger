from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.flags import Module as FlagsModule
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application was compiled with PIE \
support",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"PIE"

    def run(self):
        result = {
            "title": "Application Not Compiled With PIE Support",
            "details": "",
            "severity": "Low",
            "report": False
        }

        flags_module = FlagsModule()
        flags_module.binary = self.binary
        flags_result, flags = flags_module.run(), None
        for key in flags_result:
            if key.endswith("_flags"):
                flags = flags_result[key]

        if not flags:
            return {"print": "Couldn't get flags from binary."}

        Log.info("Analysing Flags")
        matches = re.findall(self._regex, flags)
        if not matches:
            result.update({
                "report": True,
                "details": "PIE flag not found."
            })

        return {
            "{}_result".format(self.name()): result
        }


