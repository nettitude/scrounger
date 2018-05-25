from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Decrypts and pulls a binary application",
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

    _remote = "/tmp"

    def run(self):
        Log.info("Checking if the application is installed")

        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            # set filenames
            filename = "{}/{}.bin".format(self.output, self.identifier)
            remote_filename = "{}/{}.bin".format(self._remote, self.identifier)

            # decrypt binary and move the binary
            Log.info("Decryptuing the binary")
            decrypted_bin_path = self.device.decrypt_binary(self.identifier)
            self.device.execute("mv {} {}".format(decrypted_bin_path,
                remote_filename))

            Log.info("Pulling the binary")
            # get the application into the host
            self.device.get(remote_filename, filename)

            return {
                "{}_decrypted_binary".format(self.identifier): filename,
                "{}_remote_decrypted_binary".format(
                    self.identifier): remote_filename,
                "print": "Decrypted binary saved in {}.".format(filename)
            }

        return {"print": "Application not installed."}

