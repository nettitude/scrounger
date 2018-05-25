from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements communicates over \
unencrypted channels",
        "certainty": 80
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        },
        {
            "name": "ignore",
            "description": "domains to ignore, seperated by ;",
            "required": False,
            "default": "www.w3;xmlpull.org;www.slf4j"
        }
    ]

    _regex = r"http://(-\.)?([^\"^\s/?\.#-]+\.?)+(/[^\s]*)?"

    def run(self):
        result = {
            "title": "Application Communicates Over Unencrypted Channels",
            "details": "",
            "severity": "Medium",
            "report": False
        }
        ignore = [url.strip() for url in self.ignore.split(";")]

        Log.info("Getting application's strings")
        strs = strings(self.binary)

        Log.info("Analysing strings")
        report_matches = []
        matches = re.finditer(self._regex, strs)
        for item in matches:
            match = item.group()
            if any(iurl in match for iurl in ignore) or match == "http://":
                continue
            report_matches += [match]

        print(report_matches)

        if report_matches:
            result.update({
                "report": True,
                "details": "The following strings were found:\n* {}".format(
                    "\n* ".join(sorted(set(report_matches))))
            })

        return {
            "{}_result".format(self.name()): result
        }

