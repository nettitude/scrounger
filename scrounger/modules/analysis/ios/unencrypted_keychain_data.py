from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.entitlements import Module as EModule
from scrounger.modules.misc.ios.keychain_dump import Module as KeychainModule
from scrounger.utils.config import Log
from langdetect import detect_langs
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application saves unencrypted data in \
the keychain",
        "certainty": 70
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        },
        {
            "name": "identifier",
            "description": "the application's identifier",
            "required": True,
            "default": None
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        },
        {
            "name": "min_percentage",
            "description": "percentage of certainty required to be language",
            "required": True,
            "default": 90
        },
    ]

    def run(self):
        result = {
            "title": "Application Saves Unencrypted Data In Keychain",
            "details": "",
            "severity": "Low",
            "report": False
        }

        Log.info("Getting keychain's IDs")

        ent_module = EModule()
        ent_module.binary = self.binary
        ent_result, entitlements = ent_module.run(), None
        for key in ent_result:
            if key.endswith("_entitlements"):
                entitlements = ent_result[key]

        if not entitlements:
            return {"print": "Couldn't get entitlements from the bianry."}

        keychain_id = self.identifier
        if "keychain-access-groups" in entitlements:
            keychain_id = entitlements["keychain-access-groups"]

        keychain_module = KeychainModule()
        keychain_module.device = self.device
        keychain_module.output = None
        keychain_result = keychain_module.run()
        keychain_data = keychain_result["keychain_data"]

        data = []
        for key in keychain_data:
            if (key["entitlement_group"] and \
            keychain_id in key["entitlement_group"]) or (key["account"] and \
            keychain_id in key["account"]) or (key["service"] and \
            keychain_id in key["service"]):
                data += [str(key['keychain_data'])]

        report_data = []
        for item in data:
            lang = detect_langs(item)[0]
            if lang.prob > float("0.{}".format(self.min_percentage)):
                report_data += [item]

        if report_data:
            result.update({
                "report": True,
                "details": "The following data was found:\n* {}".format(
                    "\n* ".join(report_data))
            })

        return {
            "{}_result".format(self.name()): result
        }

