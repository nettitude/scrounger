from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.android import parsed_providers

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Tests exported providers for path traversal \
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
            "name": "exploit_path",
            "description": "the path to use as exploit",
            "required": True,
            "default": "../../../../../../../../../../../../../../etc/hosts"
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
            "title": "Application's Providers Are Vulnerable To Path Traversal",
            "details": "",
            "severity": "High",
            "report": False
        }

        Log.info("Extracting and translating providers")
        providers = parsed_providers(self.decompiled_apk)

        Log.info("Analysing providers")

        vulnerable_providers = []
        example_result = None
        for provider in providers:
            exec_result = self.device.read_provider(provider,
                self.exploit_path)

            if exec_result and "Exception" not in exec_result:
                vulnerable_providers += [provider]
                example_result = exec_result

        if vulnerable_providers:
            details = "* Vulnerable Providers:\n* {}".format(
                "\n* ".join(vulnerable_providers))
            details += "\n\nAn example of exploitation success:\n{}".format(
                example_result)

            result.update({
                "report": True,
                "details": details
            })

        return {
            "{}_result".format(self.name()): result
        }

