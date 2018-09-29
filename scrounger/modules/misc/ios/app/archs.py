from scrounger.core.module import BaseModule

# helper modules
from scrounger.utils.ios import otool_archs, jtool_archs
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's available architectures",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's binary",
            "required": True,
            "default": None
        },
    ]

    def run(self):
        identifier = self.binary.rsplit("/", 1)[-1]

        Log.info("Getting archs")
        try:
            archs = otool_archs(self.binary)
        except Exception as e:
            result.update({"exceptions": [e]})
            Log.info("Trying jtool")
            archs = jtool_archs(self.binary)

        result = {
            "{}_archs".format(identifier): archs
        }

        return result

