from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application detects debuggers",
        "certainty": 75
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"ptrace"

    def run(self):
        result = {
            "title": "Application Does Not Detect Debuggers",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        Log.info("Getting binary strings")
        strs = strings(self.binary)

        Log.info("Analysing Strings")
        if not re.search(self._regex, strs):
            result.update({
                "report": True,
                "details": "No evidence of the application trying to detect \
debuggers being attached."
            })

        return {
            "{}_result".format(self.name()): result
        }

