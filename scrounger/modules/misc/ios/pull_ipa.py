from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Pulls the IPA file from a remote device",
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
            "required": True,
            "default": None
        },
    ]

    def run(self):
        Log.info("Checking if the application is installed")

        installed_apps = self.device.apps()
        if self.identifier in installed_apps:
            filename = "{}/{}.ipa".format(self.output, self.identifier)

            # decrypt ipa
            Log.info("Decrypting application")
            remote_ipa_file = self.device.decrypt(self.identifier)

            if not remote_ipa_file:
                return {"print": "Could not decrypt the application: {}".format(
                    remote_ipa_file)}

            Log.info("Pulling application's IPA")
            # get the application and delete the remote one
            self.device.get(remote_ipa_file, filename)
            self.device.execute("rm -rf {}".format(remote_ipa_file))

            return {
                "{}_local_ipa".format(self.identifier): filename,
                "print": "IPA file saved in {}.".format(filename)
            }

        return {"print": "Application not installed."}