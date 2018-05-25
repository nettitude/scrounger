from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks the application's files have the backup flag on",
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
        }
    ]

    def run(self):
        result = {
            "title": "Application Allows Files To Be Backed Up",
            "details": "",
            "severity": "Low",
            "report": False
        }

        Log.info("Checking if the application is installed")
        installed_apps = self.device.apps()

        if self.identifier not in installed_apps:
            return {"print": "Application not installed."}

        remote_data_path = installed_apps[self.identifier]["data"]

        files = self.device.find_files(remote_data_path)

        report_files = []
        for file_path in files:
            if file_path:
                protection = self.device.backup_flag(file_path)
                if protection and "0" in protection:
                    report_files += [file_path]

        if report_files:
            result.update({
                "report": True,
                "details": "The following files were found to have the \
backup flag:\n* {}".format("\n* ".join(report_files))
            })

        return {
            "{}_result".format(self.name()): result
        }

