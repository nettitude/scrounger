from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.ios import otool_symbols, jtool_symbols
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's symbols out of an installed \
application on the device",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's decrypted binary",
            "required": True,
            "default": None
        },
        {
            "name": "output",
            "description": "local output directory",
            "required": False,
            "default": None
        },
    ]

    def run(self):
        identifier = self.binary.rsplit("/", 1)[-1]

        result = {}

        Log.info("Getting application's symbols")
        try:
            symbols = otool_symbols(self.binary)
        except Exception as e:
            result.update({"exceptions": [e]})
            Log.info("Trying jtool")
            symbols = jtool_symbols(self.binary)

        result.update({
            "{}_symbols".format(identifier): symbols
        })

        if hasattr(self, "output") and self.output:
            Log.info("Saving symbols to file")
            filename = "{}/{}.symbols".format(self.output, identifier)
            with open(filename, "w") as fp:
                fp.write(symbols)

            result.update({
                "print": "Symbols saved in {}.".format(filename),
                "{}_symbols_file".format(identifier): filename
            })

        return result

