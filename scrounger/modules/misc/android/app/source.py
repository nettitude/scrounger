from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.android.app.jar import Module as JarModule

from scrounger.utils.general import execute
from scrounger.utils.android import source
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Reverses the application java classes from the JAR \
file",
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

        # get the jar first
        jar_module = JarModule()
        jar_module.output = self.output
        jar_module.apk = self.apk
        result = jar_module.run()

        self.jar = [result[jar] for jar in result if jar.endswith("_jar")][0]
        if not self.jar:
            return {"print": "Could not decompile the application"}

        Log.info("Creating source directory")
        # create source directory
        identifier = self.jar.rsplit("/", 1)[-1].lower().rsplit(".", 1)[0]

        output_path = "{}/{}.source".format(self.output, identifier)
        execute("mkdir -p {}".format(output_path))

        # unzip
        Log.info("Getting application's source")
        source(self.jar, output_path)

        return {
            "{}_source".format(identifier): output_path,
            "print": "Application source reversed to {}".format(output_path)
        }

