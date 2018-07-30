from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings, pretty_grep
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses insecure channels",
        "certainty": 50
    }

    options = [
        {
            "name": "class_dump",
            "description": "local path to the application's class dump",
            "required": True,
            "default": None
        },
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"SSLSetEnabledCiphers|TLSMinimumSupportedProtocol|\
TLSMaximumSupportedProtocol"

    def run(self):
        result = {
            "title": "Application Communicates Over Insecure Channels",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        Log.info("Getting application's strings")
        strs = strings(self.binary)

        Log.info("Analysing strings and class dump")
        if not re.search(self._regex, strs) and \
        not pretty_grep(self._regex, self.class_dump):
            result.update({
                "report": True,
                "details": "No evidence of secure channels being used."
            })

        return {
            "{}_result".format(self.name()): result
        }

