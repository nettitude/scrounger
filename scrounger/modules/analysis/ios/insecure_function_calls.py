from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.local.app.symbols import Module as SymbolsModule
from scrounger.utils.config import Log
import re

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses insecure function calls",
        "certainty": 75
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        },
        {
            "name": "function_calls",
            "description": "function calls considered insecure, seperated by |",
            "required": True,
            "default": "malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|\
StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|\
swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|\
wcstok|wmemcpy"
        }
    ]

    def run(self):
        result = {
            "title": "Application Makes Insecure Function Calls",
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
        matches = re.findall(self.function_calls, symbols)
        if matches:
            result.update({
                "report": True,
                "details": "The following function symbols were \
found: * {}".format("\n* ".join(sorted(set(matches))))
            })

        return {
            "{}_result".format(self.name()): result
        }


