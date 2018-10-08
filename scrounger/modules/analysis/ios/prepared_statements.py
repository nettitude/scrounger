from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.app.symbols import Module as SymbolsModule
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses sqlite calls and if so \
checks if it also uses prepared statements",
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

    _sqlite_regex = r"sqlite"
    _regex = r"sqlite3_prepare|sqlite3_bind_text"

    def run(self):
        result = {
            "title": "Application Does Not Use Prepared Statements",
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
        sqlite_matches = re.findall(self._sqlite_regex, symbols)
        matches = re.findall(self._regex, symbols)
        if sqlite_matches and not matches:
            result.update({
                "report": True,
                "details": "Evidences of SQLite being used were found but no \
evidence of prepared statements being used was found."
            })

        return {
            "{}_result".format(self.name()): result
        }


