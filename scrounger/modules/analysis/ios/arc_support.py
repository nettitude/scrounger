from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.symbols import Module as SymbolsModule
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if a binary was compiled with ARC support",
        "certainty": 90
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        }
    ]

    _regex = r"_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|\
_objc_retain|_objc_unretain|_objc_release|_objc_autorelease"

    def run(self):
        result = {
            "title": "Application Was Compiled Without ARC Support",
            "details": "",
            "severity": "Medium",
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
        if not re.search(self._regex, symbols):
            result.update({
                "report": True,
                "details": "No evidence of ARC functions found."
            })

        return {
            "{}_result".format(self.name()): result
        }

