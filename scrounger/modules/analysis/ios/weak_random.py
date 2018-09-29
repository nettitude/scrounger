from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.symbols import Module as SymbolsModule
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if a binary uses weak random functions",
        "certainty": 50
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"_srand|_random"

    def run(self):
        result = {
            "title": "Application Uses Weak Random Functions",
            "details": "",
            "severity": "Low",
            "report": False
        }

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
                "details": "The following evidence were found:\n* {}".format(
                    "\n* ".join(sorted(set(matches))))
            })

        return {
            "{}_result".format(self.name()): result
        }

