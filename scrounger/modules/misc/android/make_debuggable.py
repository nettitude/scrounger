from scrounger.core.module import BaseModule

from scrounger.utils.android import recompile
from scrounger.utils.general import execute
from scrounger.utils.config import Log

from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.modules.misc.android.sign_apk import Module as SignApkModule

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Makes an applicationd ebuggable by changing the \
AndroidManifest.xml file",
        "certainty": 100
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        },
        {
            "name": "output",
            "description": "local output directory to save the new app to",
            "required": False,
            "default": None
        },
        {
            "name": "install",
            "description": "set to True to install the new app",
            "required": False,
            "default": False
        },
        {
            "name": "device",
            "description": "the remote device",
            "required": False,
            "default": None
        }
    ]

    def run(self):

        Log.info("Checking output folders")
        if not self.output:
            self.output = "/tmp/scrounger-tmp"

        # create the required dirs
        execute("mkdir -p {}".format(self.output))

        # get identifier
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        manifest = manifest_module.run()
        if "print" not in manifest:
            manifest = manifest.popitem()[1]
            identifier = manifest.package()

        # set filenames
        debuggable_apk = "{}/{}-debuggable.apk".format(self.output, identifier)

        # read manifest content
        Log.info("Modifying AndroidManifest.xml")
        with open(manifest.file_path(), "r") as fd:
            manifest_content = fd.read()

        # look for <application> and modify debuggable
        new_manifest_content = ""
        for line in manifest_content.split("\n"):
            if "<application" in line:
                if "debuggable" in line:
                    line = line.replace("android:debuggable=\"false\"",
                        "android:debuggable=\"true\"")
                else:
                    line_split = line.split(">", 1)
                    line = "{} android:debuggable=\"true\">{}".format(
                        line_split[0], line_split[1])

            new_manifest_content = "{}\n{}".format(new_manifest_content, line)

        new_manifest_content = "\n".join(new_manifest_content.split("\n")[1:])

        # overwrite the manifest with the new content
        with open(manifest.file_path(), "w") as fd:
            fd.write(new_manifest_content)

        # recompiled the application
        Log.info("Re-compiling application")
        output = recompile(self.decompiled_apk, debuggable_apk)

        if "Exception" in output:
            return {
                "print": "Failed to re-compile the application:\n{}".format(
                    output)
            }

        # signing the application
        sign_module, signed_apk = SignApkModule(), None
        sign_module.recompiled_apk = debuggable_apk
        sign_module.output = self.output
        sign_result = sign_module.run()
        for key in sign_result:
            if key.endswith("_signed"):
                signed_apk = sign_result[key]

        if signed_apk:
            execute("mv {} {}".format(signed_apk, debuggable_apk))

        # install the application
        if self.install:
            Log.info("Uninstalling previously installed application")
            self.device.uninstall(identifier)

            Log.info("Installing new debuggable application")
            self.device.install(debuggable_apk)

        return {
            "{}_debuggable".format(identifier): debuggable_apk,
            "print": "Application re-compiled and signed to {}".format(
                debuggable_apk)
        }


