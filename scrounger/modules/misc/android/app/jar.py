from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.general import execute
from scrounger.utils.android import jar
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Decompiles the APK dex classes into a JAR file",
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
            "name": "apk",
            "description": "local path to the APK file",
            "required": True,
            "default": None
        }
    ]

    def run(self):
        # create decompiled directory
        identifier = self.apk.rsplit("/", 1)[-1].lower().rsplit(".", 1)[0]

        Log.info("Creating output directory")
        filename = "{}/{}.jar".format(self.output, identifier)
        execute("mkdir -p {}".format(self.output))

        # get jar
        Log.info("Getting application's jar")
        jar(self.apk, filename)

        return {
            "{}_jar".format(identifier): filename,
            "print": "Application JAR saved to {}".format(filename)
        }

