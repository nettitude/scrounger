from scrounger.core.module import BaseModule

from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Pulls the APK file from a remote device",
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
            filename = "{}/{}.apk".format(self.output, self.identifier)

            Log.info("Creating remote temp directory")

            # set up remote tmp directory
            remote_dir = "/sdcard/scrounger-tmp"
            self.device.execute("mkdir -p {}".format(remote_dir))

            # pull apk
            Log.info("Pulling apk file")
            self.device.pull_apk(self.identifier, remote_dir, filename)

            # clean tmp directory
            Log.info("Cleanign up remote directory")
            self.device.execute("rm -rf {}".format(remote_dir))

            return {
                "{}_local_apk".format(self.identifier): filename,
                "print": "APK file saved in {}".format(filename)
            }

        return {"print": "Application not installed"}