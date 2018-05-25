from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import execute
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Pulls the application's data from a remote device",
        "certainty": 100
    }

    options = [
        {
            "name": "output",
            "description": "local output directory",
            "required": True,
            "default": None
        },
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
        }
    ]

    def run(self):
        if self.device.installed(self.identifier):
            # set filenames
            output_path = "{}/{}.data".format(self.output, self.identifier)

            Log.info("Setting up remote temp directory")
            # set up remote tmp directory
            remote_dir = "/sdcard/scrounger-tmp"
            self.device.execute("mkdir -p {}".format(remote_dir))

            Log.info("Pulling data content")
            # pull data
            self.device.pull_data_contents(self.identifier, remote_dir,
                output_path)

            Log.info("Cleaning up remote device")
            # clean tmp directory
            self.device.execute("rm -rf {}".format(remote_dir))

            return {
                "{}_local_data".format(self.identifier): output_path,
                "print": "Data files saved in {}".format(output_path)
            }

        return {"print": "Application not installed"}