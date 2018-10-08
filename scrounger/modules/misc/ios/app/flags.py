from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.ios import otool_flags, jtool_flags, application_path

from scrounger.utils.config import Log


class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's compilation flags using local \
tools. Will look for otool and jtool in the PATH.",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's binary",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        identifier = self.binary.rsplit("/", 1)[-1]

        result = {}

        Log.info("Getting the flags")
        try:
            flags = otool_flags(self.binary)
        except Exception as e:
            result.update({"exceptions": [e]})
            Log.info("Trying jtool")
            flags = jtool_flags(self.binary)

        result.update({
            "{}_flags".format(identifier): flags
        })

        return result

