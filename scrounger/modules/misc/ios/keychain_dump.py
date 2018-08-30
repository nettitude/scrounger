from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.general import execute
from json import dumps

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Dumps contents from the connected device's keychain",
        "certainty": 100
    }

    options = [
        {
            "name": "device",
            "description": "the remote device",
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
        Log.info("Creating output directories")

        execute("mkdir -p {}".format(self.output))

        Log.info("Pulling keychain data")
        keychain_data = self.device.keychain_data()

        result = {
            "keychain_data": keychain_data
        }

        if hasattr(self, "output") and self.output:
            filename = "{}/keychain.json".format(self.output)

            Log.info("Saving keychain data")
            with open(filename, "w") as fp:
                fp.write(dumps(keychain_data, ensure_ascii=False))

            result.update({
                "keychain_file": filename,
                "print": "Keychain data saved in {}.".format(filename)
            })

        return result


