from scrounger.core.module import BaseModule

#helper functions
from scrounger.utils.ios import plist_dict_to_xml, plist
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if there are any Application Transport Security \
misconfigurations",
        "certainty": 90
    }

    options = [
        {
            "name": "info",
            "description": "path to a local Info.plist file",
            "required": True,
            "default": None
        }
    ]

    _ats_key = "NSAppTransportSecurity"
    _insecure_options = [
        "NSAllowsArbitraryLoads",
        "NSExceptionAllowsInsecureHTTPLoads",
        "NSThirdPartyExceptionAllowsInsecureHTTPLoads"
    ]

    def run(self):
        result = {
            "title": "Application Has Insecure ATS Configurations",
            "details": "",
            "severity": "Medium",
            "report": False
        }

        info_content = plist(self.info)

        Log.info("Parsing Info.plist file contents")
        ats_xml = plist_dict_to_xml(info_content, self._ats_key)

        Log.info("Analysing Info.plist file")
        if self._ats_key not in info_content or not info_content[self._ats_key]:
            result.update({
                "report": True,
                "details": "No evidence of ATS being implemented found."
            })

        if any(option in ats_xml for option in self._insecure_options):
            result.update({
                "report": True,
                "details": "The following insecure ATS configuration was \
found : {}".format(ats_xml)
            })

        return {
            "{}_result".format(self.name()): result
        }

