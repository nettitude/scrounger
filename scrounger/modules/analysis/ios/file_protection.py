from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks the application's files specific protection \
flags",
        "certainty": 90
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
            "name": "protection_flag",
            "description": "the required protection flag for the app's files",
            "required": True,
            "default": "NSFileProtectionComplete"
        }
    ]

    def run(self):
        result = {
            "title": "Application Files Without Protection Flags",
            "details": "",
            "severity": "Low",
            "report": False
        }

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()
        if self.identifier not in installed_apps:
            return {"print": "Application not installed."}

        remote_data_path = installed_apps[self.identifier]["data"]
        remote_app_path = installed_apps[self.identifier]["application"]

        files = self.device.find_files("{} {}".format(remote_app_path,
            remote_data_path))

        report_files = []
        for file_path in files:
            if file_path:
                protection = self.device.file_protection(file_path)
                if protection and self.protection_flag not in protection:
                    report_files += ["{} ({})".format(file_path, protection)]

        if report_files:
            result.update({
                "report": True,
                "details": "The following files were found:\n* {}".format(
                    "\n* ".join(report_files))
            })

        return {
            "{}_result".format(self.name()): result
        }

