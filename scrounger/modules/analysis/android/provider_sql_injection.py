from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.android import parsed_providers

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Tests exported providers for sql injection \
vulnerabilities",
        "certainty": 80
    }

    options = [
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        },
        {
            "name": "exploit_query",
            "description": "the query to use as exploit",
            "required": True,
            "default": "\\'"
        },
        {
            "name": "success_string",
            "description": "string to look for on a successful attack",
            "required": True,
            "default": "unrecognized token"
        },
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        result = {
            "title": "Application's Providers Are Vulnerable To SQL Injection",
            "details": "",
            "severity": "High",
            "report": False
        }

        Log.info("Extracting and translating providers")
        providers = parsed_providers(self.decompiled_apk)

        Log.info("Analysing providers")

        vulnerable_providers = []
        for provider in providers:
            exec_result = self.device.query_provider(
                provider, projection=self.exploit_query)

            if self.success_string not in exec_result[0] and \
            self.success_string not in exec_result[1]:
                exec_result = self.device.query_provider(
                    provider, selection=self.exploit_query)

            if self.success_string in exec_result[0] or \
            self.success_string in exec_result[1]:
                vulnerable_providers += [provider]

        if vulnerable_providers:
            details = "* Vulnerable Providers:\n * {}".format(
                "\n* ".join(vulnerable_providers))
            details += "\n\nAn example of exploitation success:\n{}".format(
                exec_result)

            result.update({
                "report": True,
                "details": details
            })

        return {
            "{}_result".format(self.name()): result
        }

