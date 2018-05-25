from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import pretty_grep
from scrounger.utils.android import smali_dirs
from scrounger.utils.android import extract_smali_method
from scrounger.utils.config import Log

import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application implements ssl pinning",
        "certainty": 50
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        },
        {
            "name": "ignore",
            "description": "paths to ignore, seperated by ;",
            "required": False,
            "default": "/com/google/;/android/support/"
        }
    ]

    regex = r"X509TrustManager|getAcceptedIssuers|checkClientTrusted|\
checkServerTrusted"
    mock_check_server = r".method.*checkServerTrusted(.*\n)*?[ \t]*\.\
prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*return-void"
    mock_accepted_issuers = r".method.*getAcceptedIssuers(.*\n)*?[ \t]*\.\
prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*const\/4 v0, 0x0\n[ \n\t]*\
return-object v0"

    def run(self):
        result = {
            "title": "Application Does Not Implement SSL Pinning",
            "details": "",
            "severity": "High",
            "report": False
        }

        # preparing variable to run
        ssl_keywords = {}
        ignore = [filepath.strip() for filepath in self.ignore.split(";")]

        Log.info("Identifying smali directories")
        dirs = smali_dirs(self.decompiled_apk)

        Log.info("Analysing application's smali for SSL evidences")
        for directory in dirs:
            smali = "{}/{}".format(self.decompiled_apk, directory)
            ssl_keywords.update(pretty_grep(self.regex, smali))

        if not ssl_keywords:
            result.update({
                "report": True,
                "details": "Found no evidences of a `TrustManager`."
            })

        Log.info("Analysing SSL evidences")

        for filename in ssl_keywords:
            if any(filepath in filename for filepath in ignore):
                continue

            with open(filename, "r") as fp:
                smali = fp.read()

            if re.search(self.mock_check_server, smali):
                result.update({
                    "report": True,
                    "details": "{}\n* {}:{}\n".format(
                        result["details"],
                        filename.replace(self.decompiled_apk, ""),
                        extract_smali_method("checkServerTrusted", filename)
                    )
                })

            if re.search(self.mock_accepted_issuers, smali):
                result.update({
                    "report": True,
                    "details": "{}\n* {}:{}\n".format(
                        result["details"],
                        filename.replace(self.decompiled_apk, ""),
                        extract_smali_method("getAcceptedIssuers", filename)
                    )
                })

        return {
            "{}_result".format(self.name()): result
        }
