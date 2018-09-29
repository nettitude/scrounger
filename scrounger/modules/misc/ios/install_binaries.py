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
            "description": "list of bianries to install - seperated by ;",
            "required": True,
            "default": "dump_backup_flag;dump_file_protection;\
dump_keychain;dump_log;listapps"
        },
        {
            "name": "repositories",
            "description": "the repositories needed to install the packages",
            "required": True,
            "default": "https://cydia.angelxwind.net;\
https://shmoo419.github.io/;http://cydia.ichitaso.com/"
        },
        {
            "name": "packages",
            "description": "list of packages to install - seperated by ;",
            "required": True,
            "default": "gdb71050;com.shmoo.uncrypt11;com.linusyang.appinst\
net.angelxwind.appsyncunified;com.kjcracks.clutch2;zip"
        }
    ]

    def run(self):
        Log.info("Installing binaries")
        binaries_to_install = self.binaries.split(";")
        packages_to_install = self.packages.split(";")
        repositories_to_install = self.repositories.split(";")
        binaries_local_path = "{}/bin/ios".format(_SCROUNGER_HOME)

        for binary in binaries_to_install:
            installed = self.device.install_binary("{}/{}".format(
                binaries_local_path, binary))

            if not installed:
                Log.error("Could not install {}".format(binary))

        scrounger_apt_list = "/etc/apt/sources.list.d/scrounger.list"
        repositories_list = " ".join(self.device.repositories())

        Log.info("Adding repositories")
        for repository in repositories_to_install:
            if repository not in repositories_list:
                Log.info("Adding {} repository".format(repository))
                if not repository.endswith("/"):
                    repository = "{}/".format(repository)
                self.device.execute("echo deb {} ./ >> {}".format(
                    repository, scrounger_apt_list))
                self.device.execute("apt update")

        packages = " ".join(packages_to_install)
        Log.info("Trying to install {}".format(packages))
        self.device.execute(
            "apt -y --allow-unauthenticated install {}".format(packages))

        return {
            "print": "Binaries installed."
        }

