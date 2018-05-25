from scrounger.core.module import BaseModule

# helper functions
from scrounger.utils.config import Log
from scrounger.utils.ios import otool_class_dump_to_dict
from scrounger.utils.ios import save_class_dump
from scrounger.utils.general import execute

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Dumps the classes out of a decrypted binary",
        "certainty": 100
    }

    options = [
        {
            "name": "binary",
            "description": "application's decrypted binary",
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
            "name": "output",
            "description": "local output directory",
            "required": False,
            "default": None
        },
    ]

    def run(self):
        Log.info("Dumping classes with otool")
        class_dump = otool_class_dump_to_dict(
            self.device.otool("-ov", self.binary)[0]) # stdout

        dump_name = self.binary.rsplit("/", 1)[-1].replace(" ", ".")
        result = {
            "{}_class_dump".format(dump_name.replace(".", "_")): class_dump
        }

        if hasattr(self, "output") and self.output:
            Log.info("Saving classes to file")
            dump_path = "{}/{}.class.dump".format(self.output, dump_name)

            # create output folder
            execute("mkdir -p {}".format(dump_path))

            save_class_dump(class_dump, dump_path)

            result.update({
                "{}_dump_path".format(dump_name.replace(".", "_")): dump_path,
                "print": "Dump saved in {}.".format(dump_path)
            })

        return result