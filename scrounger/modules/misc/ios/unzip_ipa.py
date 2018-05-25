from scrounger.core.module import BaseModule

# helper functions
from scrounger.modules.misc.ios.local.app.info import Module as InfoModule
from scrounger.utils.config import Log
from scrounger.utils.general import execute
from scrounger.utils.ios import unzip, application_path

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Unzips the IPA file into the output directory",
        "certainty": 100
    }

    options = [
        {
            "name": "ipa",
            "description": "local path to the IPA file",
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
        # create unzipped directory
        identifier = self.ipa.rsplit("/", 1)[-1].lower().rsplit(".", 1)[0]

        Log.info("Crating output directories")
        output_path = "{}/{}.unzipped".format(self.output, identifier)
        execute("mkdir -p {}".format(output_path))

        # unzip
        Log.info("Unzipping application")
        unzip(self.ipa, output_path)

        # get new identifier
        app_path = application_path(output_path)

        # get info
        info_module = InfoModule()
        info_module.unzipped_ipa = output_path
        info = info_module.run()
        for key in info:
            if key.endswith("_info"):
                info = info[key]
                break

        # move to new directory
        if "CFBundleIdentifier" in info:
            identifier = info["CFBundleIdentifier"]
            old_output_path = output_path
            output_path = "{}/{}.unzipped".format(self.output, identifier)
            execute("mv {} {}".format(old_output_path, output_path))

        return {
            "{}_unzipped".format(identifier): output_path,
            "print": "Application unzipped to {}".format(output_path)
        }

