from scrounger.core.module import BaseModule

# helper functions
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
            "name": "output",
            "description": "local output directory",
            "required": False,
            "default": None
        },
    ]

    def run(self):
        result = {"print": "Application not installed."}

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            # setup filenames
            remote_binary = "{}/{}".format(
                installed_apps[self.identifier]["application"],
                installed_apps[self.identifier]["binary_name"])

            Log.info("Getting application's symbols")
            symbols = self.device.otool("-Iv", remote_binary)[0] # stdout

            result = {
                "{}_symbols".format(self.identifier): symbols
            }

            if hasattr(self, "output") and self.output:
                Log.info("SAving symbols to file")

                filename = "{}/{}.symbols".format(self.output, self.identifier)
                with open(filename, "w") as fp:
                    fp.write(symbols)

                result.update({
                    "print": "Symbols saved in {}.".format(filename),
                    "{}_symbols_file".format(self.identifier): filename
                })

        return result

