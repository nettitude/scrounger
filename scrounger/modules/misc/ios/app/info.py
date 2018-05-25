from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.ios import plist_dict_to_xml
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Pulls the Info.plist info from the device",
        "certainty": 100
    }

    options = [
        {
            "name": "identifier",
            "description": "application's identifier",
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

            Log.info("Getting Info.plist contents")
            # get plist info
            info_plist = self.device.plist("{}/Info.plist".format(
                installed_apps[self.identifier]["application"]))

            result = {
                "{}_info".format(self.identifier): info_plist
            }

            if hasattr(self, "output") and self.output:
                Log.info("Saving Info.plist to json file")
                filename = "{}/{}.info.xml".format(
                    self.output, self.identifier)

                with open(filename, "w") as fp:
                    fp.write(plist_dict_to_xml(info_plist))

                result.update({
                    "{}_info_file".format(self.identifier): filename,
                    "print": "Info file saved in {}.".format(filename)
                })

        return result

