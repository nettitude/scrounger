from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log, _SCROUNGER_HOME

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Installs iOS binaries required to run some checks",
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
            "name": "binaries",
            "description": "list of bianries to install - semerated by ;",
            "required": True,
            "default": "clutch;dump_backup_flag;dump_file_protection;\
dump_keychain;dump_log;ldid"
        }
    ]

    def run(self):
        Log.info("Installing binaries")
        binaries_to_install = self.binaries.split(";")
        binaries_local_path = "{}/bin/ios".format(_SCROUNGER_HOME)

        for binary in binaries_to_install:
            installed = self.device.install_binary("{}/{}".format(
                binaries_local_path, binary))

            if not installed:
                Log.error("Could not install {}".format(binary))

        return {
            "print": "Binaries installed."
        }

