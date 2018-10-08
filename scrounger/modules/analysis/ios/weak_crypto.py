from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.symbols import Module as SymbolsModule
from scrounger.utils.config import Log
from scrounger.utils.general import strings
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses weak crypto",
        "certainty": 60
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"kCCAlgorithmDES|kCCAlgorithm3DES|kCCAlgorithmRC2|\
kCCAlgorithmRC4|kCCOptionECBMode|kCCOptionCBCMode|DES|3ES|RC2|RC4|ECB|CBC"

    def run(self):
        result = {
            "title": "Application Uses Weak Crypto Functions",
            "details": "",
            "severity": "High",
            "report": True
        }

        Log.info("Getting application's strings")
        strs = strings(self.binary)

        symb_module = SymbolsModule()
        symb_module.binary = self.binary
        symbols_result, symbols = symb_module.run(), None
        for key in symbols_result:
            if key.endswith("_symbols"):
                symbols = symbols_result[key]

        if not symbols:
            return {"print": "Couldn't get symbols from binary."}

        Log.info("Analysing Symbols")
        matches = re.findall(self._regex, symbols)

        if matches:
            result.update({
                "report": True,
                "details": "The following evidences were found:\n* {}".format(
                    "\n* ".join(sorted(set(matches)))
                )
            })

        Log.info("Analysing strings")
        matches = re.findall(self._regex, strs)

        if matches:
            result.update({
                "report": True,
                "details": "{}\n* {}".format(result["details"],
                    "\n* ".join(sorted(set(matches))))
            })

        return {
            "{}_result".format(self.name()): result
        }

