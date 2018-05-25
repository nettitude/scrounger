from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings, pretty_grep
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements SSL pinning",
        "certainty": 60
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

    _regex = r"setAllowInvalidCertificates|allowsInvalidSSLCertificate|\
validatesDomainName|SSLPinningMode"

    def run(self):
        result = {
            "title": "The Application Does Not Implement SSL Pinning",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        Log.info("Getting application's strings")
        strs = strings(self.binary)

        Log.info("Analysing strings and class dump")
        matches = re.findall(self._regex, strs)
        evidence = pretty_grep(self._regex, self.class_dump)

        if matches:
            result.update({
                "report": True,
                "details": "The following strings were found:\n* {}".format(
                    "\n* ".join(sorted(set(matches))))
            })

        if evidence:
            result.update({
                "report": True,
                "details": "{}\nThe following was found in the class dump:\n\
{}".format(result["details"], pretty_grep_to_str(evidence, self.class_dump))
            })

        return {
            "{}_result".format(self.name()): result
        }

