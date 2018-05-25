from scrounger.core.module import BaseModule

# helper functions / modules
from scrounger.modules.misc.android.app.manifest import Module as ManifestModule
from scrounger.utils.config import Log

class Module(BaseModule):
    meta = {
        "author": "RDC",
        "description": "Checks for secret codes in the application",
        "certainty": 90
    }

    options = [
        {
            "name": "decompiled_apk",
            "description": "local folder containing the decompiled apk file",
            "required": True,
            "default": None
        }
    ]

    _secret_code_activity = "android.provider.Telephony.SECRET_CODE"

    def run(self):
        result = {
            "title": "Application Has Secret Codes",
            "details": "",
            "severity": "Low",
            "report": False
        }

        # create manifest
        manifest_module = ManifestModule()
        manifest_module.decompiled_apk = self.decompiled_apk
        self.manifest = manifest_module.run()
        if "print" in self.manifest:
            return {"print": "Could not get the manifest"}

        self.manifest = self.manifest.popitem()[1]

        Log.info("Analysing application's manifest for secret codes")
        secret_codes = self.manifest.secret_codes()

        if secret_codes:
            details = "* Secret Codes:\n * {}".format("\n * ".join(
                secret_codes))
            details += """

* Test the secret codes using the following command:
adb shell su -c "am broadcast -a {} -d android_secret_code://CODE"
            """.format(self._secret_code_activity)
            result.update({"report": True, "details": details})

        return {
            "{}_result".format(self.name()): result,
            "{}_secret_codes".format(
                self.manifest.package()): secret_codes
        }

