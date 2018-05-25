from scrounger.core.module import BaseModule

from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks if the application uses native libraries",
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
            "name": "libs",
            "description": "paths to the libraries directories",
            "required": True,
            "default": "lib/arm;lib/arm64"
        }
    ]

    def run(self):
        result = {
            "title": "Application Uses Native Libraries",
            "details": "",
            "severity": "Low",
            "report": False
        }

        Log.info("Identifying application's libraries")
        libs_path = [lib.strip() for lib in self.libs.split(";")]

        libraries = []
        if self.device.installed(self.identifier):
            app_path = self.device.packages()[self.identifier].rsplit("/", 1)[0]

            libs_path_str = " ".join([
                "{}/{}".format(app_path, lib) for lib in libs_path
            ])

            libraries = [
                lib for lib in self.device.root_execute(
                    "ls {}".format(libs_path_str))[0].split("\n")
            ]

        if libraries:
            result.update({
                "report": True,
                "details": "* {}".format("\n* ".join(libraries))
            })

        return {
            "{}_result".format(self.name()): result
        }

