from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import strings, pretty_grep, pretty_grep_to_str
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements jailbreak \
detection",
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

    _regex = r"jailb[a-zA-Z0-9_-]*"

    artefacts = [
        "/bin/bash",
        "/usr/sbin/sshd",
        "/Applications/Cydia.app",
        "/private/var/lib/apt",
        "/pangueaxe",
        "/System/Library/LaunchDaemons/io.pangu.axe.untether.plist",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/usr/libexec/sftp-server",
        "/private/var/stash",
        "cydia",
        "substrate",
        "jailb"
    ]

    def run(self):
        result = {
            "title": "Application Does Not Implement Jailbreak Detection",
            "details": "",
            "severity": "High",
            "report": True
        }

        # update regex with artefacts, base64 and hex
        for artefact in self.artefacts:
            self._regex = "{}|{}|{}|{}".format(self._regex, artefact,
                artefact.encode("base64"), artefact.encode("hex")
            ).replace("\n", "").replace("=", "").replace("+", "\\+")
            # need to escape + because of the regex grep

        Log.info("Getting application's strings")
        strs = strings(self.binary)

        Log.info("Analysing strings and class dump")
        matches = re.findall(self._regex, strs)
        evidence = pretty_grep(self._regex, self.class_dump)

        if matches:
            result.update({
                "title": "Application Implements Jailbreak Detection",
                "details": "The following strings were found:\n* {}".format(
                    "\n* ".join(sorted(set(matches))))
            })

        if evidence:
            result.update({
                "title": "Application Implements Jailbreak Detection",
                "details": "{}\nThe following was found in the class dump:\n\
{}".format(result["details"], pretty_grep_to_str(evidence, self.class_dump))
            })

        return {
            "{}_result".format(self.name()): result
        }

