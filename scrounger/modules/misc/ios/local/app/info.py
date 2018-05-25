from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.ios import plist, application_path, plist_dict_to_xml
from scrounger.utils.config import Log
from os.path import exists as _exists

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Pulls the Info.plist info from the unzipped IPA file \
and saves an XML file with it's contents to the output folder",
        "certainty": 100
    }

    options = [
        {
            "name": "unzipped_ipa",
            "description": "local folder containing the unzipped ipa file",
            "required": True,
            "default": None
        },
        {
            "name": "output",
            "description": "local output directory",
            "required": False,
            "default": None
        },
    ]

    def run(self):
        result = {"print": "Could not find Info.plist."}

        Log.info("Looking for Info.plist file")
        app_path = application_path(self.unzipped_ipa)

        filename = "{}/Info.plist".format(app_path)
        if _exists(filename):
            Log.info("Parsing Info.plist file")
            # get plist info
            info_plist = plist(filename)
            identifier = info_plist["CFBundleIdentifier"]

            result = {
                "{}_info".format(identifier): info_plist
            }

            if hasattr(self, "output") and self.output:
                Log.info("Converting Info.plist to XML file")
                filename = "{}/{}.info.xml".format(self.output, identifier)
                with open(filename, "w") as fp:
                    fp.write(plist_dict_to_xml(info_plist))

                result.update({
                    "{}_info_file".format(identifier): filename,
                    "print": "Info file saved in {}.".format(filename)
                })

        return result

