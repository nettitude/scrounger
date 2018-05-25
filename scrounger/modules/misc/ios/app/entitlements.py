from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's entitlements",
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
                installed_apps[self.identifier]["display_name"])

            Log.info("Getting entitlements")
            entitlements = self.device.ldid("-e", remote_binary)[0] # stdout

            result = {
                "{}_entitlements".format(self.identifier): entitlements
            }

            if hasattr(self, "output") and self.output:
                Log.info("Saving entitlements to file")

                filename = "{}/{}.entitlements".format(self.output,
                    self.identifier)

                with open(filename, "w") as fp:
                    fp.write(entitlements)

                result.update({
                    "print": "Entitlements saved in {}.".format(filename),
                    "{}_entitlements_file".format(self.identifier): filename
                })

        return result

