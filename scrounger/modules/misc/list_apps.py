from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import execute

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Lists installed applications on the remote device",
        "certainty": 100
    }

    options = [
        {
            "name": "output",
            "description": "local output directory",
            "required": False,
            "default": None
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        installed_apps = self.device.apps()

        result = {
            "print": "Applications installed on {}:\n{}".format(
                self.device.device_id(),
                "\n".join(installed_apps)),
            "{}_installed_apps".format(self.device.device_id()): installed_apps
        }

        if hasattr(self, "output") and self.output:
            filename = "{}/{}.installed.apps".format(self.output,
                self.device.device_id())

            # write file
            with open(filename, "w") as fp:
                fp.write("\n".join(installed_apps))

            result["print"] += "\nInstalled applications saved in {}.".format(
                filename)

        return result

