from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's data from the remote device",
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
            "required": True,
            "default": None
        },
    ]

    def run(self):
        result = {"print": "Application not installed."}

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            # setup filenames
            remote_app_path = installed_apps[self.identifier]["data"]
            output_path = "{}/{}.data".format(self.output, self.identifier)

            Log.info("Creating output directories")
            # create output folder
            execute("mkdir -p {}".format(output_path))

            Log.info("Pulling application's data contents")
            self.device.pull_data_contents(remote_app_path, output_path)

            result.update({
                "print": "Data saved in {}.".format(output_path),
                "{}_data".format(self.identifier): output_path
            })

        return result

