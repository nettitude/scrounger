from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.ios import entitlements, plist_dict_to_xml
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Gets the application's entitlements from a local \
binary and saves them to file",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "local path to the application's binary",
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
        identifier = self.binary.rsplit("/", 1)[-1]

        Log.info("Getting entitlements")
        ents = entitlements(self.binary)

        result = {
            "{}_entitlements".format(identifier): ents
        }

        if hasattr(self, "output") and self.output:
            Log.info("Saving entitlements to file")
            filename = "{}/{}.entitlements".format(self.output, identifier)
            with open(filename, "w") as fp:
                fp.write(plist_dict_to_xml(ents))

            result.update({
                "print": "Entitlements saved in {}.".format(filename),
                "{}_entitlements_file".format(identifier): filename
            })

        return result

